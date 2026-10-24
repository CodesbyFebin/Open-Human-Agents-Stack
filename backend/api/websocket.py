"""Redis pub/sub bridge between Go mesh event envelopes and FastAPI WebSockets."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis
import structlog
from fastapi import WebSocket

log = structlog.get_logger()
CHANNEL = "openminds:events"


def normalize_event(payload: Any) -> dict[str, Any]:
    """Normalize Go MeshEventPayload and native Python event shape without code execution."""
    if not isinstance(payload, dict):
        raise ValueError("Expected JSON event object")
    if "event_type" in payload:
        if not isinstance(payload["event_type"], str) or not isinstance(payload.get("payload_data"), dict):
            raise ValueError("Invalid Go event envelope")
        return {
            "type": payload["event_type"],
            "event_uuid": payload.get("event_uuid"),
            "timestamp_epoch": payload.get("timestamp_epoch"),
            "source_engine": payload.get("source_engine"),
            "payload": payload["payload_data"],
        }
    if not isinstance(payload.get("type"), str):
        raise ValueError("Invalid native event envelope")
    return payload


class ConnectionManager:
    def __init__(self):
        self.active: set[WebSocket] = set()
        self.subscribed = False
        self.messages_received = 0
        self.last_message_at: str | None = None
        self.last_error: str | None = None

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, message: dict[str, Any]):
        dead: set[WebSocket] = set()
        for ws in tuple(self.active):
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.add(ws)
        self.active.difference_update(dead)

    def status(self) -> dict[str, Any]:
        return {
            "channel": CHANNEL,
            "subscriber_connected": self.subscribed,
            "events_received": self.messages_received,
            "last_event_at": self.last_message_at,
            "connected_clients": len(self.active),
            "last_error": self.last_error,
        }

    async def start_redis_listener(self, redis: aioredis.Redis):
        pubsub = redis.pubsub()
        try:
            await pubsub.subscribe(CHANNEL)
            self.subscribed = True
            self.last_error = None
            log.info("redis_listener_started", channel=CHANNEL)
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                try:
                    event = normalize_event(json.loads(message["data"]))
                except (ValueError, TypeError, json.JSONDecodeError) as exc:
                    log.warning("redis_event_rejected", error=str(exc))
                    continue
                self.messages_received += 1
                self.last_message_at = datetime.now(timezone.utc).isoformat()
                await self.broadcast(event)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.last_error = type(exc).__name__
            log.warning("redis_listener_stopped_unexpectedly", error=str(exc))
        finally:
            self.subscribed = False
            try:
                await pubsub.unsubscribe(CHANNEL)
                await pubsub.aclose()
            except Exception:
                pass
