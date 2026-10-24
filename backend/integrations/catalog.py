"""Read-only upstream integration catalog.

The presence of a repository in the catalog never means its service is running.
Credentials, runtime status and protected endpoints are intentionally not exposed.
"""
import json
from functools import lru_cache
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[2] / "integrations" / "upstreams.json"

@lru_cache(maxsize=1)
def all_integrations():
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return tuple(data["upstreams"])

def public_integrations():
    return [
        {
            "id": entry["id"],
            "repository": entry["repository"],
            "layer": entry["layer"],
            "license": entry["license"],
            "integration_mode": entry["mode"],
            "runtime_status": "unconfigured",
        }
        for entry in all_integrations()
    ]
