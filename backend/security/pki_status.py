"""Fail-closed certificate-material diagnostic.

This checks parseability and key match only. It does NOT assert that transport mTLS
is enabled, that a peer was authenticated, or that revocation is enforced.
"""
from __future__ import annotations

import os
import ssl
from pathlib import Path


def crypto_status() -> dict[str, bool | str]:
    ca = Path(os.getenv("MTLS_CA_CERT_PATH", "/etc/openminds/certs/ca.crt"))
    cert = Path(os.getenv("MTLS_SERVER_CERT_PATH", "/etc/openminds/certs/server.crt"))
    key = Path(os.getenv("MTLS_SERVER_KEY_PATH", "/etc/openminds/certs/server.key"))
    status: dict[str, bool | str] = {
        "material_loadable": False,
        "mutual_tls_enforced": False,
        "reason": "certificate material unavailable or invalid",
    }
    try:
        if not (ca.is_file() and cert.is_file() and key.is_file()):
            return status
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_verify_locations(cafile=str(ca))
        context.load_cert_chain(certfile=str(cert), keyfile=str(key))
        status["material_loadable"] = True
        status["reason"] = "material loadable; peer authentication not verified"
    except (OSError, ssl.SSLError, ValueError):
        pass
    return status
