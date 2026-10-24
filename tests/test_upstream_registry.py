"""Upstream provenance and disabled execution policy tests."""
import json

import pytest

from backend.integrations.upstream_registry import list_upstreams, upstream_status


def test_upstreams_have_isolated_disabled_defaults():
    projects = list_upstreams()
    assert {item["id"] for item in projects} == {"octop", "openhuman", "andee"}
    assert all(item["enabled"] is False for item in projects)
    assert upstream_status()["executing"] is False
    assert upstream_status()["verified_adapters"] == 0


def test_andee_cannot_be_marked_redistributable(tmp_path):
    projects = list_upstreams()
    for item in projects:
        if item["id"] == "andee":
            item["distribution"] = "bundled"
    path = tmp_path / "upstreams.json"
    path.write_text(json.dumps({"schema_version": 1, "projects": projects}), encoding="utf-8")
    with pytest.raises(ValueError, match="Andee distribution"):
        list_upstreams(path)


def test_unknown_integration_cannot_enable_runner(tmp_path):
    projects = list_upstreams()
    projects[0]["enabled"] = True
    path = tmp_path / "upstreams.json"
    path.write_text(json.dumps({"schema_version": 1, "projects": projects}), encoding="utf-8")
    with pytest.raises(ValueError, match="disabled"):
        list_upstreams(path)
