"""Fail-closed, container-isolated execution primitive for approved worker payloads.

This is NOT an autonomous coding agent. Jobs without a verified code artifact
are rejected, and Docker isolation is required before any supplied code runs.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path
from .queue import dequeue
from .db import execute, fetch_one

IMAGE = os.environ.get("OPENMINDS_SANDBOX_IMAGE", "python:3.12-alpine")

def run_isolated(code: str, timeout: int = 30, mem_mb: int = 256) -> dict:
    """Run Python only inside an unprivileged, network-disabled Docker container."""
    if not isinstance(code, str) or not code or len(code.encode()) > 100_000:
        raise ValueError("A bounded nonempty code artifact is required")
    if not (1 <= timeout <= 120 and 64 <= mem_mb <= 1024):
        raise ValueError("Resource limits out of range")
    with tempfile.TemporaryDirectory(prefix="openminds-job-") as td:
        src = Path(td) / "task.py"
        src.write_text(code, encoding="utf-8")
        src.chmod(0o644)
        cmd = [
            "docker", "run", "--rm", "--network", "none", "--read-only",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--pids-limit", "64", "--memory", f"{mem_mb}m", "--cpus", "1",
            "--user", "65534:65534", "--tmpfs", "/tmp:rw,nosuid,nodev,size=32m",
            "--mount", f"type=bind,src={td},dst=/work,readonly",
            "--workdir", "/work", IMAGE, "python", "-B", "/work/task.py",
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=timeout, check=False)
            return {"exit": proc.returncode, "stdout": proc.stdout[-2000:],
                    "stderr": proc.stderr[-2000:]}
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            return {"exit": -1, "stdout": "", "stderr": type(exc).__name__}

def process_job(job: dict) -> dict:
    """Reject unverified work: a task identifier alone is not executable code."""
    task_id = job.get("id")
    org_id = job.get("org_id")
    if not task_id or not org_id:
        raise ValueError("Missing task identity")
    task = fetch_one(
        "SELECT status FROM tasks WHERE id=%s AND org_id=%s",
        (task_id, org_id),
    )
    if task is None or task["status"] != "queued":
        raise ValueError("Task is missing, foreign, or not queued")
    # The current API queues only identifiers. A signed artifact and an
    # atomic durable claim protocol must be added before execution is enabled.
    return {"exit": -1, "error": "No verified executable artifact; execution denied"}

def loop():
    while True:
        job = dequeue(timeout=5)
        if not job:
            continue
        try:
            result = process_job(job)
            execute("UPDATE tasks SET status='failed', updated_at=now() "
                    "WHERE id=%s AND org_id=%s AND status='queued'",
                    (job["id"], job["org_id"]))
            execute("INSERT INTO evidence (task_id, kind, payload) "
                    "VALUES (%s, %s, %s)",
                    (job["id"], "worker_denied", json.dumps(result)))
        except Exception:
            # A production worker needs durable claim/ack + retry semantics.
            # Do not pretend this destructive pop-queue is crash recoverable.
            raise

if __name__ == "__main__":
    loop()
