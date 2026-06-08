"""Celery background worker — processes scheduled incremental delta syncs,

nightly full syncs, and manual trigger sync requests.
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from celery import Celery
from celery.schedules import crontab
from app.core.config import get_settings
from app.core.mongodb import get_mongo_db
from app.services.servicenow_client import ServiceNowClient

settings = get_settings()

celery_app = Celery(
    "regiq_worker", broker=settings.redis_url, backend=settings.redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# ── Scheduled sync schedules ──────────────────────────────
celery_app.conf.beat_schedule = {
    "delta-sync-every-15-min": {
        "task": "app.worker.delta_sync_task",
        "schedule": crontab(minute="*/15"),
    },
    "full-sync-nightly": {
        "task": "app.worker.full_sync_task",
        "schedule": crontab(minute=0, hour=2),  # 2 AM UTC
    },
    "weekly-model-retraining-beat": {
        "task": "weekly_model_retraining",
        "schedule": crontab(minute=0, hour=0, day_of_week="sunday"),  # Midnight on Sunday
    },
    "defect-sync-every-hour": {
        "task": "app.worker.defect_sync_task",
        "schedule": crontab(minute=0),  # Every hour
    },
}


def _run_async(coro):
    """Helper to run coroutines synchronously in Celery worker context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task
def delta_sync_task():
    """Incremental delta sync scheduler running every 15 minutes."""
    print("Running scheduled Delta Sync...")
    return _run_async(_run_all_syncs("delta"))


@celery_app.task
def full_sync_task():
    """Nightly full metadata sync scheduler running at 2 AM."""
    print("Running scheduled Nightly Full Sync...")
    return _run_async(_run_all_syncs("full"))


@celery_app.task
def manual_sync_task(connection_id: str, sync_type: str):
    """Manual sync triggered from API connection management panel."""
    print(f"Running manual sync {sync_type} for connection {connection_id}")
    return _run_async(_run_single_sync(connection_id, sync_type))


# ── Execution Logic ──────────────────────────────────────


async def _run_all_syncs(sync_type: str) -> dict:
    mongo = get_mongo_db()
    cursor = mongo.servicenow_connections.find({"status": "connected"})
    connections = await cursor.to_list(length=100)

    results = []
    for conn in connections:
        res = await _perform_sync(conn, sync_type)
        results.append(res)
    return {"status": "completed", "sync_type": sync_type, "results": results}


async def _run_single_sync(connection_id: str, sync_type: str) -> dict:
    mongo = get_mongo_db()
    conn = await mongo.servicenow_connections.find_one({"id": connection_id})
    if not conn:
        return {"status": "failed", "error": "Connection not found"}
    res = await _perform_sync(conn, sync_type)
    return res


async def _perform_sync(conn: dict, sync_type: str) -> dict:
    mongo = get_mongo_db()
    conn_id = conn["id"]

    client = ServiceNowClient(
        instance_url=conn["instance_url"],
        client_id=conn["client_id"],
        client_secret_encrypted=conn["client_secret_encrypted"],
    )

    started_at = datetime.now(timezone.utc)

    # Perform connection health monitoring with auto-reconnect
    is_healthy = await client.check_health()
    if not is_healthy:
        await mongo.servicenow_connections.update_one(
            {"id": conn_id}, {"$set": {"status": "unhealthy"}}
        )
        return {
            "connection_id": conn_id,
            "status": "failed",
            "error": "ServiceNow instance connection health check failed",
        }

    try:
        last_sync = conn.get("last_sync_at")
        if not last_sync:
            last_sync = started_at - timedelta(days=1)
        elif isinstance(last_sync, str):
            last_sync = datetime.fromisoformat(last_sync)

        # Polling/Retrieval of updates
        changes = await client.poll_delta_changes(last_sync)
        completed_at = datetime.now(timezone.utc)

        # Update Neo4j graph with newly retrieved metadata changes
        try:
            from app.services.graph_builder import GraphBuilderService

            builder = GraphBuilderService()
            builder.process_metadata_batch(changes)
            module_rows = await client.fetch_module_metadata("incident")
            builder.process_metadata_batch(module_rows)
            builder.ensure_module_scaffold("incident")
        except Exception as graph_err:
            print(f"Error updating Neo4j graph during sync: {graph_err}")

        # Update last sync time
        await mongo.servicenow_connections.update_one(
            {"id": conn_id},
            {
                "$set": {
                    "last_sync_at": completed_at,
                    "status": "connected",
                    "last_checked_at": completed_at,
                }
            },
        )

        # Log details to sync history collection in MongoDB
        sync_doc = {
            "connection_id": conn_id,
            "sync_type": sync_type,
            "status": "completed",
            "started_at": started_at,
            "completed_at": completed_at,
            "components_synced": len(changes),
            "errors": [],
            "tenant_id": conn["tenant_id"],
        }
        await mongo.sync_history.insert_one(sync_doc)

        return {
            "connection_id": conn_id,
            "status": "success",
            "sync_type": sync_type,
            "components_synced": len(changes),
        }

    except Exception as e:
        completed_at = datetime.now(timezone.utc)
        error_msg = str(e)

        sync_doc = {
            "connection_id": conn_id,
            "sync_type": sync_type,
            "status": "failed",
            "started_at": started_at,
            "completed_at": completed_at,
            "components_synced": 0,
            "errors": [error_msg],
            "tenant_id": conn["tenant_id"],
        }
        await mongo.sync_history.insert_one(sync_doc)

        return {"connection_id": conn_id, "status": "failed", "error": error_msg}

@celery_app.task(name="weekly_model_retraining")
def weekly_model_retraining_task():
    """Trigger the weekly batch retraining pipeline from celery."""
    import subprocess
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Starting weekly model retraining...")
    try:
        subprocess.run(["python", "scripts/train_classifier.py"], check=True)
        logger.info("Weekly model retraining completed successfully.")
    except Exception as e:
        logger.error(f"Weekly model retraining failed: {e}")


@celery_app.task
def defect_sync_task():
    """Automatically run hourly defect sync across active tenants/sources."""
    import logging
    from app.core.database import async_session_factory
    from app.models.tenant import Tenant
    from app.schemas.defect import DefectImportRequest
    from app.api.v1.defects import import_defects
    from sqlalchemy import select

    logger = logging.getLogger(__name__)
    logger.info("Starting periodic background defect sync...")

    async def _sync():
        async with async_session_factory() as db:
            result = await db.execute(select(Tenant))
            tenants = result.scalars().all()
            
            # Simple mock user object to satisfy FastAPI dependency requirements
            class MockUser:
                def __init__(self, tenant_id, user_id):
                    self.tenant_id = tenant_id
                    self.id = user_id

            for tenant in tenants:
                # Mock a tenant user for the context
                mock_user = MockUser(tenant.id, tenant.id)
                for source in ["jira", "ado", "servicenow"]:
                    try:
                        logger.info(f"Syncing {source} defects for tenant {tenant.id}")
                        req = DefectImportRequest(source=source, config={})
                        await import_defects(body=req, db=db, current_user=mock_user)
                    except Exception as ex:
                        logger.error(f"Failed to sync {source} for tenant {tenant.id}: {ex}")
            await db.commit()

    return _run_async(_sync())