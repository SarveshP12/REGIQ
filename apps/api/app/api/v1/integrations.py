"""ServiceNow Integration endpoints — /api/v1/integrations."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit
from app.core.database import get_db
from app.core.mongodb import get_mongo_db
from app.core.security import get_current_user, require_permissions
from app.models.user import User
from app.schemas.servicenow import (
    IntegrationHealthResponse,
    ServiceNowConnect,
    ServiceNowConnectionResponse,
    SyncStatusResponse,
    SyncTrigger,
)

router = APIRouter()


# ── In-memory connection store (for Phase 1 MVP; production would use DB table) ─


_connections: dict[str, dict] = {}


# ── Register ServiceNow instance ─────────────────────────


@router.post(
    "/servicenow/connect",
    response_model=ServiceNowConnectionResponse,
    status_code=201,
    dependencies=[Depends(require_permissions("integrations:write"))],
)
async def connect_servicenow(
    body: ServiceNowConnect,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a ServiceNow instance connection."""
    conn_id = uuid.uuid4()

    # Store connection metadata in MongoDB for persistence
    mongo = get_mongo_db()
    conn_doc = {
        "id": str(conn_id),
        "name": body.name,
        "instance_url": body.instance_url,
        "client_id": body.client_id,
        # Never store client_secret in plain text in production — use a vault
        "client_secret_hash": "***masked***",
        "environment": body.environment,
        "tenant_id": str(current_user.tenant_id),
        "status": "connected",
        "last_sync_at": None,
        "created_at": datetime.now(timezone.utc),
    }
    await mongo.servicenow_connections.insert_one(conn_doc)

    await log_audit(
        db, current_user.id, "create", "servicenow_connection",
        resource_id=conn_id, tenant_id=current_user.tenant_id,
        details={"instance_url": body.instance_url, "environment": body.environment},
    )

    return ServiceNowConnectionResponse(
        id=conn_id,
        name=body.name,
        instance_url=body.instance_url,
        environment=body.environment,
        status="connected",
        last_sync_at=None,
        created_at=conn_doc["created_at"],
    )


# ── Trigger manual sync ──────────────────────────────────


@router.post(
    "/servicenow/sync",
    response_model=SyncStatusResponse,
    dependencies=[Depends(require_permissions("integrations:write"))],
)
async def trigger_sync(
    body: SyncTrigger,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a manual sync for a ServiceNow connection."""
    mongo = get_mongo_db()
    conn = await mongo.servicenow_connections.find_one({"id": str(body.connection_id)})
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    now = datetime.now(timezone.utc)

    # Record sync job in MongoDB
    sync_doc = {
        "connection_id": str(body.connection_id),
        "sync_type": body.sync_type,
        "status": "pending",  # Async via Celery
        "started_at": now,
        "completed_at": None,
        "components_synced": 0,
        "errors": [],
        "tenant_id": str(current_user.tenant_id),
    }
    await mongo.sync_history.insert_one(sync_doc)
    
    # Trigger Celery task
    from app.worker import manual_sync_task
    manual_sync_task.delay(str(body.connection_id), body.sync_type)

    # Update last_sync_at on the connection
    await mongo.servicenow_connections.update_one(
        {"id": str(body.connection_id)},
        {"$set": {"last_sync_at": now, "status": "connected"}},
    )

    await log_audit(
        db, current_user.id, "sync", "servicenow_connection",
        resource_id=body.connection_id, tenant_id=current_user.tenant_id,
        details={"sync_type": body.sync_type},
    )

    return SyncStatusResponse(
        connection_id=body.connection_id,
        sync_type=body.sync_type,
        status="completed",
        started_at=now,
        completed_at=now,
        components_synced=0,
        errors=[],
    )


# ── Integration health ───────────────────────────────────


@router.get(
    "/health",
    response_model=IntegrationHealthResponse,
    dependencies=[Depends(require_permissions("integrations:read"))],
)
async def integration_health(
    current_user: User = Depends(get_current_user),
):
    """Check the health of all ServiceNow integrations for this tenant."""
    mongo = get_mongo_db()
    connections = await mongo.servicenow_connections.find(
        {"tenant_id": str(current_user.tenant_id)},
        {"_id": 0, "client_secret_hash": 0},
    ).to_list(length=50)

    statuses = [c.get("status", "unknown") for c in connections]
    if not connections:
        overall = "no_connections"
    elif all(s == "connected" for s in statuses):
        overall = "healthy"
    elif any(s == "connected" for s in statuses):
        overall = "degraded"
    else:
        overall = "unhealthy"

    return IntegrationHealthResponse(
        connections=connections,
        overall_status=overall,
        last_check=datetime.now(timezone.utc),
    )
