"""Capability-controlled tool execution gate."""
from fastapi import HTTPException

ALLOWED = {
    "read_file": {"roles": ["member", "admin"], "approval": False},
    "write_file": {"roles": ["admin"], "approval": True},
    "shell": {"roles": ["admin"], "approval": True},
}

def check(tool: str, role: str, approved: bool = False):
    spec = ALLOWED.get(tool)
    if not spec:
        raise HTTPException(403, f"Tool not allowed: {tool}")
    if role not in spec["roles"]:
        raise HTTPException(403, f"Role {role} cannot use {tool}")
    if spec["approval"] and not approved:
        raise HTTPException(403, f"Tool {tool} requires human approval")
    return True
