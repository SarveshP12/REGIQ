"""Audit logging middleware — auto-logs all mutations to the audit_logs table."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_audit(
    db: AsyncSession,
    user_id: uuid.UUID,
    action: str,
    resource_type: str,
    resource_id: Optional[uuid.UUID] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    tenant_id: Optional[uuid.UUID] = None,
) -> AuditLog:
    """Write an audit log entry for any mutation."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address or "unknown",
        tenant_id=tenant_id,
    )
    db.add(entry)
    await db.flush()
    return entry
