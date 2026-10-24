"""No-device safety tests; not a substitute for physical device qualification."""
import subprocess

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.mobile import device_bridge

app = FastAPI()
app.include_router(device_bridge.router)
client = TestClient(app)
ID = "emulator-5554"
TOKEN = "dedicated-test-token-with-32-characters"


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("OM_MOBILE_ENABLE", raising=False)
    response = client.get("/api/mobile/frame-buffer", params={"device_id": ID})
    assert response.status_code == 503


def test_rejects_wrong_device_and_credential(monkeypatch):
    monkeypatch.setenv("OM_MOBILE_ENABLE", "1")
    monkeypatch.setenv("OM_MOBILE_DEVICE_ID", ID)
    monkeypatch.setenv("OM_MOBILE_TOKEN", TOKEN)
    assert client.get("/api/mobile/frame-buffer", params={"device_id": "other"}, headers={"Authorization": "Bearer " + TOKEN}).status_code == 404
    assert client.get("/api/mobile/frame-buffer", params={"device_id": ID}, headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_authorized_frame_uses_fixed_argv_and_returns_real_bytes(monkeypatch):
    monkeypatch.setenv("OM_MOBILE_ENABLE", "1")
    monkeypatch.setenv("OM_MOBILE_DEVICE_ID", ID)
    monkeypatch.setenv("OM_MOBILE_TOKEN", TOKEN)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, device_bridge.PNG_MAGIC + b"\x00" * 64, b"")

    monkeypatch.setattr(device_bridge.subprocess, "run", fake_run)
    response = client.get("/api/mobile/frame-buffer", params={"device_id": ID}, headers={"Authorization": "Bearer " + TOKEN})
    assert response.status_code == 200
    assert response.content.startswith(device_bridge.PNG_MAGIC)
    assert response.headers["cache-control"] == "no-store"
    assert calls == [["adb", "-s", ID, "exec-out", "screencap", "-p"]]


def test_touch_relay_fails_closed():
    assert client.post("/api/mobile/touch").status_code == 403
