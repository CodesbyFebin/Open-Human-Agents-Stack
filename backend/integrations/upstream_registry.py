"""Read-only registry for separately distributed, disabled-by-default upstream runtimes.

No subprocess execution, dynamic loading, network access or secret handling occurs here.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REGISTRY_PATH = Path(__file__).resolve().parents[2] / "integrations" / "upstreams.json"
VALID_INTEGRATIONS = {"standalone-service", "separate-process-evaluation", "local-only-evaluation"}


def list_upstreams(path: Path = REGISTRY_PATH) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported upstream registry schema")
    projects = data.get("projects")
    if not isinstance(projects, list):
        raise ValueError("Invalid upstream projects list")
    seen: set[str] = set()
    for item in projects:
        if not isinstance(item, dict):
            raise ValueError("Invalid upstream project")
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier.isidentifier() or identifier in seen:
            raise ValueError("Invalid or duplicate upstream id")
        seen.add(identifier)
        if item.get("integration") not in VALID_INTEGRATIONS:
            raise ValueError("Unrecognized integration boundary")
        if item.get("enabled") is not False:
            raise ValueError("Third-party integrations must be explicitly disabled by default")
        if not str(item.get("url", "")).startswith("https://github.com/"):
            raise ValueError("Only canonical GitHub source URLs are permitted")
        if item["id"] == "andee" and item.get("distribution") != "never-bundle-without-written-permission":
            raise ValueError("Andee distribution restriction must be preserved")
    return projects


def upstream_status() -> dict[str, Any]:
    """Expose evaluation metadata only; never claim a runtime is installed or running."""
    return {"upstreams": list_upstreams(), "executing": False, "verified_adapters": 0}
