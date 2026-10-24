"""MCP Tool Authorization — durable, server-side, no self-approval."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import text

from backend.db import async_session

log = structlog.get_logger()


class MCPAuthenticator:
    """All MCP tool approvals are stored in PostgreSQL.
    
    A caller CANNOT self-approve. Only users with role='admin' or
    role='reviewer' can grant tool approvals. Approvals are durable
    and survive restarts.
    """

    async def approve(self, tool_name: str, approved_by: str, scope: str = "*") -> None:
        """Grant approval for a tool. Caller must be admin/reviewer."""
        async with async_session() as s:
            # Verify the approver's role
            row = await s.execute(
                text("SELECT role FROM users WHERE id = :id"), {"id": approved_by}
            )
            role = row.scalar_one_or_none()
            if role not in ("admin", "reviewer"):
                raise PermissionError(f"User {approved_by} (role={role}) cannot approve tools")

            # Insert approval (idempotent: upsert)
            await s.execute(
                text("INSERT INTO tool_approvals (tool_name, approved_by, scope) "
                     "VALUES (:t, :a, :s) "
                     "ON CONFLICT DO NOTHING"),
                {"t": tool_name, "a": approved_by, "s": scope},
            )
            await s.commit()
            log.info("tool_approved", tool=tool_name, by=approved_by, scope=scope)

    async def revoke(self, tool_name: str, revoked_by: str) -> None:
        """Revoke a tool approval."""
        async with async_session() as s:
            row = await s.execute(
                text("SELECT role FROM users WHERE id = :id"), {"id": revoked_by}
            )
            role = row.scalar_one_or_none()
            if role not in ("admin", "reviewer"):
                raise PermissionError("Only admin/reviewer can revoke")

            await s.execute(
                text("UPDATE tool_approvals SET is_active = FALSE WHERE tool_name = :t"),
                {"t": tool_name},
            )
            await s.commit()

    async def is_approved(self, tool_name: str) -> bool:
        """Check if a tool has an active approval."""
        async with async_session() as s:
            row = await s.execute(
                text("SELECT 1 FROM tool_approvals WHERE tool_name = :t AND is_active = TRUE "
                     "AND (expires_at IS NULL OR expires_at > now()) LIMIT 1"),
                {"t": tool_name},
            )
            return row.first() is not None

    async def validate_call(self, tool_name: str, caller_id: str) -> bool:
        """Validate that a caller is authorized to use a tool.
        
        CRITICAL: The caller's own 'approved' flag is IGNORED.
        Only the server-side record in tool_approvals matters.
        """
        # Check if tool is approved at all
        if not await self.is_approved(tool_name):
            log.warning("mcp_call_denied", tool=tool_name, caller=caller_id, reason="tool_not_approved")
            return False

        # Check if caller is authorized (in production: check scope, caller role, etc.)
        # For v1.0: any authenticated user can call an approved tool
        return True
