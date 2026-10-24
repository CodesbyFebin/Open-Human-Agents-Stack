"""Durable job runner: claim, execute, checkpoint, retry, cancel."""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import text

from backend.db import async_session

log = structlog.get_logger()

# Docker isolation: jobs execute in ephemeral containers
DOCKER_IMAGE = os.getenv("JOB_EXECUTOR_IMAGE", "python:3.11-slim")
WORKSPACE_BASE = "/tmp/openminds/worktrees"


class JobRunner:
    """Manages the full durable job lifecycle."""

    async def submit(self, type: str, payload: dict, max_retries: int = 3, idempotency_key: str | None = None) -> str:
        """Submit a new job. Returns job_id."""
        async with async_session() as s:
            result = await s.execute(
                text("INSERT INTO jobs (type, payload, max_retries, idempotency_key) "
                     "VALUES (:t, :p, :mr, :ik) RETURNING id"),
                {"t": type, "p": json.dumps(payload), "mr": max_retries, "ik": idempotency_key},
            )
            await s.commit()
            return str(result.scalar())

    async def claim_and_execute(self, job_id: str) -> dict:
        """Claim a job (atomic) and execute it in Docker isolation."""
        async with async_session() as s:
            # Atomic claim: only one worker can claim
            result = await s.execute(
                text("UPDATE jobs SET status='claimed', claimed_by=:worker, claimed_at=now() "
                     "WHERE id=:id AND status IN ('pending','retrying') RETURNING id, type, payload, retry_count"),
                {"worker": "local-01", "id": job_id},
            )
            await s.commit()
            row = result.mappings().first()

        if not row:
            return {"status": "skipped", "reason": "already claimed or terminal"}

        # Mark running
        await self._update_status(job_id, "running")

        try:
            output = await self._execute_in_docker(row["type"], json.loads(row["payload"]))
            await self._complete(job_id, output)
            return {"status": "completed", "output": output}
        except Exception as e:
            await self._fail(job_id, str(e), row["retry_count"])
            return {"status": "failed", "error": str(e)}

    async def _execute_in_docker(self, job_type: str, payload: dict) -> dict:
        """Execute job in an ephemeral Docker container with filesystem isolation."""
        workspace = f"{WORKSPACE_BASE}/{uuid.uuid4().hex[:8]}"
        os.makedirs(workspace, exist_ok=True)

        # Write task spec into the container
        spec_path = f"{workspace}/task.json"
        with open(spec_path, "w") as f:
            json.dump(payload, f)

        # Build the Docker command
        cmd = [
            "docker", "run", "--rm",
            "--network", "none",  # No network access (isolation)
            "--memory", "512m",
            "--cpus", "1",
            "-v", f"{workspace}:/workspace:rw",
            DOCKER_IMAGE,
            "python", "-c",
            self._get_executor_script(job_type),
        ]

        # Execute with timeout
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

            if proc.returncode != 0:
                raise RuntimeError(f"Job failed (exit {proc.returncode}): {stderr.decode()[:500]}")

            # Read output from workspace
            output_path = f"{workspace}/output.json"
            if os.path.exists(output_path):
                with open(output_path) as f:
                    return json.load(f)
            return {"stdout": stdout.decode()[:5000]}

        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError("Job timed out after 300s")
        finally:
            # Cleanup workspace
            import shutil
            shutil.rmtree(workspace, ignore_errors=True)

    def _get_executor_script(self, job_type: str) -> str:
        """Return the Python script that runs inside the container."""
        if job_type == "coding_task":
            return (
                "import json, os\n"
                "with open('/workspace/task.json') as f: task = json.load(f)\n"
                "# In production: invoke Pydantic AI agent here\n"
                "result = {'summary': f'Executed: {task.get(chr(116)+chr(97)+chr(115)+chr(107), chr(63))[:50]}', 'files_modified': [], 'diff': ''}\n"
                "with open('/workspace/output.json', 'w') as f: json.dump(result, f)\n"
            )
        return "print('unknown job type')\n"

    async def _update_status(self, job_id: str, status: str):
        async with async_session() as s:
            await s.execute(text("UPDATE jobs SET status=:s, started_at=now() WHERE id=:id"), {"s": status, "id": job_id})
            await s.commit()

    async def _complete(self, job_id: str, output: dict):
        async with async_session() as s:
            await s.execute(
                text("UPDATE jobs SET status='completed', result=:r, completed_at=now() WHERE id=:id"),
                {"r": json.dumps(output), "id": job_id},
            )
            await s.commit()

    async def _fail(self, job_id: str, error: str, retry_count: int, max_retries: int = 3):
        """Fail a job. Retry if under max_retries."""
        async with async_session() as s:
            if retry_count < max_retries:
                # Exponential backoff: 1s, 2s, 4s
                delay_s = 2 ** retry_count
                await s.execute(
                    text("UPDATE jobs SET status='retrying', error=:e, retry_count=retry_count+1, "
                         "next_retry_at=now() + make_interval(secs=:d) WHERE id=:id"),
                    {"e": error, "d": delay_s, "id": job_id},
                )
                log.warning("job_will_retry", job_id=job_id, attempt=retry_count + 1, delay_s=delay_s)
            else:
                await s.execute(
                    text("UPDATE jobs SET status='failed', error=:e, completed_at=now() WHERE id=:id"),
                    {"e": error, "id": job_id},
                )
                log.error("job_failed_permanently", job_id=job_id, error=error)
            await s.commit()
