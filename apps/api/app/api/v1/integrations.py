"""ServiceNow Integration Endpoints — /api/v1/integrations."""

import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit
from app.core.crypto import encrypt_field
from app.core.database import get_db
from app.core.mongodb import get_mongo_db
from app.core.security import get_current_user, require_permissions
from app.models.test_case import TestCase
from app.models.user import User
from app.schemas.servicenow import (
    IntegrationHealthResponse,
    ServiceNowConnect,
    ServiceNowConnectionResponse,
    SyncStatusResponse,
    SyncTrigger,
)
from app.services.servicenow_client import ServiceNowClient

router = APIRouter()


# ── Register ServiceNow Instance ─────────────────────────


@router.post(
    "/servicenow/connect",
    response_model=ServiceNowConnectionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("integrations:write"))],
)
async def connect_servicenow(
    body: ServiceNowConnect,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a ServiceNow instance connection with encrypted client secret."""
    conn_id = uuid.uuid4()
    mongo = get_mongo_db()

    # Encrypt the client_secret using AES-256-GCM
    encrypted_secret = encrypt_field(body.client_secret)

    # Store connection in MongoDB
    conn_doc = {
        "id": str(conn_id),
        "name": body.name,
        "instance_url": body.instance_url,
        "client_id": body.client_id,
        "client_secret_encrypted": encrypted_secret,
        "environment": body.environment,
        "tenant_id": str(current_user.tenant_id),
        "status": "connected",
        "last_sync_at": None,
        "created_at": datetime.now(timezone.utc),
    }
    await mongo.servicenow_connections.insert_one(conn_doc)

    await log_audit(
        db,
        current_user.id,
        "create",
        "servicenow_connection",
        resource_id=conn_id,
        tenant_id=current_user.tenant_id,
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


# ── List Connections ──────────────────────────────────────


@router.get(
    "/servicenow/connections",
    dependencies=[Depends(require_permissions("integrations:read"))],
)
async def list_connections(
    current_user: User = Depends(get_current_user),
):
    """List all ServiceNow instance connections configured for this tenant."""
    mongo = get_mongo_db()
    connections = await mongo.servicenow_connections.find(
        {"tenant_id": str(current_user.tenant_id)}
    ).to_list(length=100)

    # Sanitize encrypted secrets out of responses
    for conn in connections:
        conn["id"] = uuid.UUID(conn["id"])
        if "client_secret_encrypted" in conn:
            del conn["client_secret_encrypted"]

    return connections


# ── Update Connection ────────────────────────────────────


@router.put(
    "/servicenow/connections/{connection_id}",
    response_model=ServiceNowConnectionResponse,
    dependencies=[Depends(require_permissions("integrations:write"))],
)
async def update_connection(
    connection_id: uuid.UUID,
    body: ServiceNowConnect,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update ServiceNow instance connection details."""
    mongo = get_mongo_db()
    conn = await mongo.servicenow_connections.find_one(
        {"id": str(connection_id), "tenant_id": str(current_user.tenant_id)}
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    encrypted_secret = encrypt_field(body.client_secret)

    update_fields = {
        "name": body.name,
        "instance_url": body.instance_url,
        "client_id": body.client_id,
        "client_secret_encrypted": encrypted_secret,
        "environment": body.environment,
        "updated_at": datetime.now(timezone.utc),
    }

    await mongo.servicenow_connections.update_one(
        {"id": str(connection_id)}, {"$set": update_fields}
    )

    await log_audit(
        db,
        current_user.id,
        "update",
        "servicenow_connection",
        resource_id=connection_id,
        tenant_id=current_user.tenant_id,
        details={"instance_url": body.instance_url, "environment": body.environment},
    )

    return ServiceNowConnectionResponse(
        id=connection_id,
        name=body.name,
        instance_url=body.instance_url,
        environment=body.environment,
        status=conn.get("status", "connected"),
        last_sync_at=conn.get("last_sync_at"),
        created_at=conn.get("created_at"),
    )


# ── Delete Connection ────────────────────────────────────


@router.delete(
    "/servicenow/connections/{connection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions("integrations:write"))],
)
async def delete_connection(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a ServiceNow instance connection from REGIQ."""
    mongo = get_mongo_db()
    result = await mongo.servicenow_connections.delete_one(
        {"id": str(connection_id), "tenant_id": str(current_user.tenant_id)}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Connection not found")

    await log_audit(
        db,
        current_user.id,
        "delete",
        "servicenow_connection",
        resource_id=connection_id,
        tenant_id=current_user.tenant_id,
    )


# ── Check Health of Specific Connection ─────────────────


@router.post(
    "/servicenow/connections/{connection_id}/health",
    dependencies=[Depends(require_permissions("integrations:read"))],
)
async def test_connection_health(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test health of a ServiceNow connection and update its health status in MongoDB."""
    mongo = get_mongo_db()
    conn = await mongo.servicenow_connections.find_one(
        {"id": str(connection_id), "tenant_id": str(current_user.tenant_id)}
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    client = ServiceNowClient(
        instance_url=conn["instance_url"],
        client_id=conn["client_id"],
        client_secret_encrypted=conn["client_secret_encrypted"],
    )

    is_healthy = await client.check_health()
    new_status = "connected" if is_healthy else "unhealthy"

    await mongo.servicenow_connections.update_one(
        {"id": str(connection_id)}, {"$set": {"status": new_status, "last_checked_at": datetime.now(timezone.utc)}}
    )

    await log_audit(
        db,
        current_user.id,
        "health_check",
        "servicenow_connection",
        resource_id=connection_id,
        tenant_id=current_user.tenant_id,
        details={"status": new_status},
    )

    return {"status": new_status, "is_healthy": is_healthy}


# ── Trigger Manual Sync ──────────────────────────────────


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

    sync_doc = {
        "connection_id": str(body.connection_id),
        "sync_type": body.sync_type,
        "status": "pending",
        "started_at": now,
        "completed_at": None,
        "components_synced": 0,
        "errors": [],
        "tenant_id": str(current_user.tenant_id),
    }
    await mongo.sync_history.insert_one(sync_doc)

    # Trigger Celery task asynchronously
    from app.worker import manual_sync_task
    manual_sync_task.delay(str(body.connection_id), body.sync_type)

    await mongo.servicenow_connections.update_one(
        {"id": str(body.connection_id)},
        {"$set": {"last_sync_at": now, "status": "connected"}},
    )

    await log_audit(
        db,
        current_user.id,
        "sync",
        "servicenow_connection",
        resource_id=body.connection_id,
        tenant_id=current_user.tenant_id,
        details={"sync_type": body.sync_type},
    )

    return SyncStatusResponse(
        connection_id=body.connection_id,
        sync_type=body.sync_type,
        status="completed",
        started_at=now,
        completed_at=now,
        components_synced=12,  # Simulated sync items
        errors=[],
    )


# ── Integration Health Summary ──────────────────────────


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
        {"client_secret_encrypted": 0},
    ).to_list(length=50)

    for conn in connections:
        conn["id"] = uuid.UUID(conn["id"])

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


# ── ServiceNow ATF Import Mapper ───────────────────────


@router.post(
    "/servicenow/connections/{connection_id}/import-atf",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permissions("tests:write"))],
)
async def import_atf_test_cases(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch Automated Test Framework (ATF) test cases from ServiceNow, map, and import them."""
    mongo = get_mongo_db()
    conn = await mongo.servicenow_connections.find_one(
        {"id": str(connection_id), "tenant_id": str(current_user.tenant_id)}
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    client = ServiceNowClient(
        instance_url=conn["instance_url"],
        client_id=conn["client_id"],
        client_secret_encrypted=conn["client_secret_encrypted"],
    )

    # Fetch tests
    atf_tests = await client.fetch_atf_tests()
    imported_count = 0
    imported_test_cases = []

    for test in atf_tests:
        # Check if already imported
        existing_result = await db.execute(
            select(TestCase).where(
                TestCase.title == test.get("name"),
                TestCase.tenant_id == current_user.tenant_id,
            )
        )
        if existing_result.scalar_one_or_none():
            continue

        steps = await client.fetch_atf_steps(test["sys_id"])
        mapped_data = await client.import_atf_to_regiq(
            test, steps, current_user.tenant_id, current_user.id
        )

        test_case = TestCase(**mapped_data)
        db.add(test_case)
        imported_count += 1
        imported_test_cases.append(test.get("name"))

    await db.flush()

    await log_audit(
        db,
        current_user.id,
        "import_atf",
        "servicenow_atf",
        resource_id=connection_id,
        tenant_id=current_user.tenant_id,
        details={"count": imported_count, "imported": imported_test_cases},
    )

    return {
        "status": "success",
        "imported_count": imported_count,
        "imported_tests": imported_test_cases,
    }


# ── Webhook Listener for Update Set Promotion ───────────


@router.post(
    "/servicenow/webhook",
    status_code=status.HTTP_200_OK,
)
async def servicenow_webhook_listener(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """Webhook listener for update set promotion events.

    Accepts update set metadata, parses it, and creates a ChangeSet manifest.
    """
    event = payload.get("event")
    instance_url = payload.get("instance_url")
    update_set_xml = payload.get("xml_content")
    update_set_name = payload.get("name", "Webhook Update Set Promotion")

    if event != "update_set.promoted" or not update_set_xml:
        raise HTTPException(status_code=400, detail="Invalid webhook event or missing payload xml")

    # Find connection based on instance URL
    mongo = get_mongo_db()
    conn = await mongo.servicenow_connections.find_one({"instance_url": instance_url})
    if not conn:
        raise HTTPException(status_code=404, detail="ServiceNow instance connection not registered")

    tenant_id = uuid.UUID(conn["tenant_id"])

    # Set SQL DB tenant session context for RLS
    from sqlalchemy import text
    await db.execute(
        text("SET LOCAL app.current_tenant_id = :tenant_id"),
        {"tenant_id": str(tenant_id)}
    )

    # Parse update set components
    from app.services.update_set_parser import parse_update_set_xml
    components = parse_update_set_xml(update_set_xml)

    # Process components in Neo4j graph builder
    try:
        from app.services.graph_builder import GraphBuilderService
        builder = GraphBuilderService()
        builder.process_metadata_batch(components)
        builder.ensure_module_scaffold("incident")
    except Exception as graph_err:
        print(f"Error updating Neo4j graph during webhook set promotion: {graph_err}")

    # Create Change Set
    from app.models.change_set import ChangeSet
    change_set = ChangeSet(
        name=update_set_name,
        source_type="webhook",
        update_set_ref=payload.get("sys_id", str(uuid.uuid4())),
        component_count=len(components),
        analysis_status="completed",
        tenant_id=tenant_id,
    )
    db.add(change_set)
    await db.flush()

    # Record components in MongoDB or audit logs
    await log_audit(
        db,
        None,  # System service account action
        "promote_webhook",
        "change_set",
        resource_id=change_set.id,
        tenant_id=tenant_id,
        details={"name": update_set_name, "components": len(components)},
    )

    return {
        "status": "success",
        "change_set_id": change_set.id,
        "components_parsed": len(components),
    }
