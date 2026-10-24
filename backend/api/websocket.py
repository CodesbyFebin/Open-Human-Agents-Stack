"""WebSocket connection manager with Redis pub/sub fan-out."""
from __future__ import annotations

import asyncio
import json

import redis.asyncio as aioredis
import structlog
from fastapi import WebSocket

log = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections and bridges Redis pub/sub to clients."""

    def __init__(self):
        self.active: set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)
        log.info("ws_connected", total=len(self.active))

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)
        log.info("ws_disconnected", total=len(self.active))

    async def broadcast(self, message: dict):
        """Send to all locally connected clients."""
        dead = set()
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.active.discard(ws)

    async def start_redis_listener(self, redis: aioredis.Redis):
        """Subscribe to Redis and forward events to local WebSocket clients."""
        pubsub = redis.pubsub()
        await pubsub.subscribe("openminds:events")
        log.info("redis_listener_started")
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    data = json.loads(message["data"])
                    await self.broadcast(data)
                except (json.JSONDecodeError, Exception) as e:
                    log.warning("redis_listener_error", error=str(e))
        except asyncio.CancelledError:
            log.info("redis_listener_stopped")
        finally:
            await pubsub.unsubscribe("openminds:events")
            await pubsub.close()
