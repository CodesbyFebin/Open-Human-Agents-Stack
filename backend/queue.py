"""Redis-backed durable task queue."""
import os, json, redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE = "openminds:tasks"

def client():
    return redis.from_url(REDIS_URL)

def enqueue(task: dict) -> str:
    r = client()
    r.lpush(QUEUE, json.dumps(task))
    return task.get("id", "")

def dequeue(timeout=5):
    r = client()
    item = r.brpop(QUEUE, timeout=timeout)
    if not item:
        return None
    return json.loads(item[1])
