"""Mesh event wire protocol, corruption rejection and actual Redis fan-out tests."""
import asyncio
import json
import os

import pytest

from backend.api.websocket import CHANNEL, ConnectionManager, normalize_event


def test_go_event_is_normalized_without_losing_origin():
    event = normalize_event({
        "event_uuid": "event-1",
        "timestamp_epoch": 123,
        "source_engine": "go-runner",
        "event_type": "runner_heartbeat",
        "payload_data": {"runner_id": "runner-1"},
    })
    assert event["type"] == "runner_heartbeat"
    assert event["payload"]["runner_id"] == "runner-1"
    assert event["source_engine"] == "go-runner"


@pytest.mark.parametrize("payload", [[], {}, {"event_type": 1, "payload_data": {}},
                                      {"event_type": "test", "payload_data": "bad"},
                                      {"type": []}])
def test_invalid_events_rejected(payload):
    with pytest.raises(ValueError):
        normalize_event(payload)


@pytest.mark.asyncio
async def test_real_redis_mesh_delivery():
    if os.environ.get("EVENT_MESH_INTEGRATION") != "1":
        pytest.skip("Requires disposable Redis and explicit EVENT_MESH_INTEGRATION=1")
    import redis.asyncio as redis

    class Client:
        def __init__(self):
            self.messages = []

        async def send_text(self, payload):
            self.messages.append(json.loads(payload))

    connection = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    manager = ConnectionManager()
    client = Client()
    manager.active.add(client)
    task = asyncio.create_task(manager.start_redis_listener(connection))
    try:
        for _ in range(100):
            if manager.subscribed:
                break
            await asyncio.sleep(0.02)
        assert manager.subscribed
        await connection.publish(CHANNEL, json.dumps({
            "event_uuid": "e-test",
            "timestamp_epoch": 1,
            "source_engine": "test-go",
            "event_type": "integration_probe",
            "payload_data": {"safe": True},
        }))
        for _ in range(100):
            if client.messages:
                break
            await asyncio.sleep(0.02)
        assert client.messages[0]["type"] == "integration_probe"
        assert manager.status()["events_received"] >= 1
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await connection.aclose()
