"""Opt-in ADB framebuffer API for an explicitly allowlisted local device.

No remote pairing, touch execution or implicit activation occurs here.
"""
from __future__ import annotations

import hmac
import os
import re
import subprocess

from fastapi import APIRouter, Header, HTTPException, Response

router = APIRouter(prefix="/api/mobile", tags=["mobile"])
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def authorized_device(authorization: str | None, device_id: str) -> str:
    token = os.getenv("OM_MOBILE_TOKEN", "")
    allowed = os.getenv("OM_MOBILE_DEVICE_ID", "")
    if os.getenv("OM_MOBILE_ENABLE") != "1" or len(token) < 24 or not allowed:
        raise HTTPException(503, "Mobile capture is not enabled")
    if not re.fullmatch(r"[A-Za-z0-9._:-]{1,100}", device_id) or device_id != allowed:
        raise HTTPException(404, "Device not allowlisted")
    provided = authorization.removeprefix("Bearer ") if authorization and authorization.startswith("Bearer ") else ""
    if not hmac.compare_digest(provided, token):
        raise HTTPException(401, "Unauthorized mobile capture")
    return device_id


def capture_android_frame(device_id: str) -> bytes:
    result = subprocess.run(
        ["adb", "-s", device_id, "exec-out", "screencap", "-p"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        timeout=7,
    )
    if not result.stdout.startswith(PNG_MAGIC) or len(result.stdout) > 12_000_000:
        raise ValueError("ADB did not return a bounded PNG frame")
    return result.stdout


@router.get("/frame-buffer")
def frame_buffer(device_id: str, platform: str = "ANDROID", authorization: str | None = Header(default=None)):
    authorized_device(authorization, device_id)
    if platform != "ANDROID":
        raise HTTPException(422, "iOS frame capture is not implemented")
    try:
        image = capture_android_frame(device_id)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError, ValueError):
        raise HTTPException(503, "Device frame unavailable")
    return Response(content=image, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.post("/touch")
def touch_not_exposed():
    # Requires durable reviewer approval, authenticated operator identity and session binding.
    raise HTTPException(403, "Touch relay requires an approved device session")
