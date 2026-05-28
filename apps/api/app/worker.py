import os
from celery import Celery
from celery.schedules import crontab
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "regiq_worker",
    broker=settings.redis_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    "delta-sync-every-15-min": {
        "task": "app.worker.delta_sync_task",
        "schedule": crontab(minute="*/15"),
    },
    "full-sync-nightly": {
        "task": "app.worker.full_sync_task",
        "schedule": crontab(minute=0, hour=2), # 2 AM UTC
    },
}

@celery_app.task
def delta_sync_task():
    # Placeholder for delta sync logic
    print("Running Delta Sync...")
    return {"status": "success", "type": "delta"}

@celery_app.task
def full_sync_task():
    # Placeholder for full sync logic
    print("Running Full Nightly Sync...")
    return {"status": "success", "type": "full"}

@celery_app.task
def manual_sync_task(connection_id: str, sync_type: str):
    print(f"Running manual sync {sync_type} for connection {connection_id}")
    return {"status": "success", "connection_id": connection_id}

