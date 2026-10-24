"""Isolated coding worker. Consumes queue, enforces limits, records evidence."""
import os, subprocess, tempfile, json, time
from .queue import dequeue
from .db import execute

def run_isolated(code: str, timeout=30, mem_mb=256) -> dict:
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "task.py")
        open(src, "w").write(code)
        cmd = [
            "bash", "-c",
            f"ulimit -v {mem_mb * 1024}; timeout {timeout} python3 {src}"
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5, cwd=td)
            return {"exit": proc.returncode, "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]}
        except subprocess.TimeoutExpired:
            return {"exit": -1, "stdout": "", "stderr": "timeout"}

def loop():
    print("worker started")
    while True:
        job = dequeue(timeout=5)
        if not job:
            continue
        result = run_isolated(job.get("code", "print('noop')"))
        execute(
            "UPDATE tasks SET status=%s, updated_at=now() WHERE id=%s",
            ("completed" if result["exit"] == 0 else "failed", job["id"])
        )
        execute(
            """INSERT INTO evidence (task_id, kind, payload)
               VALUES (%s, %s, %s)""",
            (job["id"], "worker_result", json.dumps(result))
        )
        print("done", job["id"], result["exit"])

if __name__ == "__main__":
    loop()
