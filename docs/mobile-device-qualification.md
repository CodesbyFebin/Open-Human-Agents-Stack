# Mobile vision and framebuffer qualification

The FastAPI device bridge is disabled unless all three variables are explicitly set:

- `OM_MOBILE_ENABLE=1`
- `OM_MOBILE_DEVICE_ID` — one allowlisted locally attached Android device
- `OM_MOBILE_TOKEN` — a strong internal Bearer token (minimum 24 characters)

`GET /api/mobile/frame-buffer?device_id=...` runs `adb -s <device> exec-out screencap -p` with fixed argv, seven-second timeout and bounded PNG response. It does not expose an accessible browser endpoint because no human user-session gateway has been verified. Never put the internal token in `NEXT_PUBLIC_*` or React props. A future same-origin proxy must authenticate a human, authorize the device, enforce CSRF protections and forward on the server side only.

`POST /api/mobile/touch` is fail-closed (403). The standalone vision driver has tested coordinate validation and an Android ADB command shape, but **there is no authorized touch relay**. iOS no longer reports fictitious success.

## Still required to close issue #4

1. A physically attached Android device, ADB enrollment and host permissions.
2. End-to-end screenshot from device → authenticated session gateway → React canvas without leaking other users' frames.
3. Touch relay bound to explicit device session, human confirmation, role, rate and coordinate bounds, with audit receipts.
4. Device disconnect, locked screen, rotation, revocation and restart tests.
5. iOS implementation if iOS support is claimed, plus independent permission/privacy review.

No physical device validation or streaming performance has been claimed.
