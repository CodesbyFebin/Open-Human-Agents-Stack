"""Offline contract tests for safe upstream source import decisions."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "integrations/upstreams.json"
SCRIPT = ROOT / "scripts/fetch_upstreams.py"

def test_registry_identity_and_modes_are_unique():
    data = json.loads(REGISTRY.read_text())
    entries = data["upstreams"]
    assert len(entries) >= 20
    assert len({x["id"] for x in entries}) == len(entries)
    for item in entries:
        assert item["url"] == "https://github.com/" + item["repository"]
        assert item["mode"] in {
            "source-eligible", "dependency", "external-service",
            "restricted-service", "license-review", "candidate",
        }

def test_restricted_licenses_fail_closed_without_network(tmp_path):
    for item in ("dify", "multica", "agentsmesh", "context-mode", "taku-ui"):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--include", item,
             "--destination", str(tmp_path / item)],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert not (tmp_path / item).exists()

def test_bulk_import_is_not_default(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--destination", str(tmp_path / "upstreams")],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert not (tmp_path / "upstreams").exists()
