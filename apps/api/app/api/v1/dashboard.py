"""Dashboard & reporting endpoints — /api/v1/dashboard."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_permissions
from app.models.audit_log import AuditLog
from app.models.change_set import ChangeComponent, ChangeSet
from app.models.test_case import TestCase
from app.models.user import User
from app.schemas.dashboard import RepositoryHealthResponse, SyncStatusDashboard, UserActivityResponse
from app.core.mongodb import get_mongo_db

router = APIRouter()


# ── Test Repository Health ────────────────────────────────


@router.get(
    "/repository-health",
    response_model=RepositoryHealthResponse,
    dependencies=[Depends(require_permissions("dashboards:read"))],
)
async def repository_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard data for test repository health metrics."""
    tenant_id = current_user.tenant_id
    base = select(TestCase).where(TestCase.tenant_id == tenant_id, TestCase.archived_at.is_(None))

    # Total count
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0

    # Status distribution
    status_q = await db.execute(
        select(TestCase.status, func.count())
        .where(TestCase.tenant_id == tenant_id, TestCase.archived_at.is_(None))
        .group_by(TestCase.status)
    )
    status_dist = {row[0]: row[1] for row in status_q.all()}

    # Criticality breakdown
    crit_q = await db.execute(
        select(TestCase.criticality, func.count())
        .where(TestCase.tenant_id == tenant_id, TestCase.archived_at.is_(None))
        .group_by(TestCase.criticality)
    )
    crit_dist = {row[0]: row[1] for row in crit_q.all()}

    # Unmapped tests (no business_process_id)
    unmapped = (await db.execute(
        select(func.count()).where(
            TestCase.tenant_id == tenant_id,
            TestCase.archived_at.is_(None),
            TestCase.business_process_id.is_(None),
        )
    )).scalar() or 0

    # Stale tests (not updated in 90+ days)
    stale_cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    stale = (await db.execute(
        select(func.count()).where(
            TestCase.tenant_id == tenant_id,
            TestCase.archived_at.is_(None),
            TestCase.updated_at < stale_cutoff,
        )
    )).scalar() or 0

    # Automation breakdown
    auto_q = await db.execute(
        select(TestCase.automation_flag, func.count())
        .where(TestCase.tenant_id == tenant_id, TestCase.archived_at.is_(None))
        .group_by(TestCase.automation_flag)
    )
    auto_dist = {row[0]: row[1] for row in auto_q.all()}

    # Format distribution
    fmt_q = await db.execute(
        select(TestCase.format_type, func.count())
        .where(TestCase.tenant_id == tenant_id, TestCase.archived_at.is_(None))
        .group_by(TestCase.format_type)
    )
    fmt_dist = {row[0]: row[1] for row in fmt_q.all()}

    # Recent additions (last 7 days)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent = (await db.execute(
        select(func.count()).where(
            TestCase.tenant_id == tenant_id,
            TestCase.archived_at.is_(None),
            TestCase.created_at >= week_ago,
        )
    )).scalar() or 0

    return RepositoryHealthResponse(
        total_test_cases=total,
        status_distribution=status_dist,
        criticality_breakdown=crit_dist,
        unmapped_tests=unmapped,
        stale_test_count=stale,
        automation_breakdown=auto_dist,
        format_distribution=fmt_dist,
        recent_additions=recent,
    )


# ── Sync Status ───────────────────────────────────────────


@router.get(
    "/sync-status",
    response_model=SyncStatusDashboard,
    dependencies=[Depends(require_permissions("dashboards:read"))],
)
async def sync_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard data for ServiceNow sync status."""
    tenant_id = current_user.tenant_id
    mongo = get_mongo_db()

    # Get connections from MongoDB
    connections = await mongo.servicenow_connections.find(
        {"tenant_id": str(tenant_id)},
        {"_id": 0, "client_secret_hash": 0},
    ).to_list(length=50)

    # Change set stats from PostgreSQL
    total_cs = (await db.execute(
        select(func.count()).where(ChangeSet.tenant_id == tenant_id)
    )).scalar() or 0

    pending = (await db.execute(
        select(func.count()).where(ChangeSet.tenant_id == tenant_id, ChangeSet.analysis_status == "pending")
    )).scalar() or 0

    total_comp = (await db.execute(
        select(func.count())
        .select_from(ChangeComponent)
        .join(ChangeSet, ChangeComponent.change_set_id == ChangeSet.id)
        .where(ChangeSet.tenant_id == tenant_id)
    )).scalar() or 0

    # Last sync time from MongoDB
    last_sync = None
    for c in connections:
        ls = c.get("last_sync_at")
        if ls and (last_sync is None or ls > last_sync):
            last_sync = ls

    # Error count from sync history
    error_count = await mongo.sync_history.count_documents({
        "tenant_id": str(tenant_id),
        "status": "failed",
    })

    return SyncStatusDashboard(
        connections=connections,
        total_change_sets=total_cs,
        pending_analysis=pending,
        total_components=total_comp,
        last_sync_time=last_sync,
        error_count=error_count,
    )


# ── User Activity ────────────────────────────────────────


@router.get(
    "/user-activity",
    response_model=UserActivityResponse,
    dependencies=[Depends(require_permissions("dashboards:read"))],
)
async def user_activity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard data for user activity."""
    tenant_id = current_user.tenant_id

    # Recent audit actions
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.created_at.desc())
        .limit(20)
    )
    recent_logs = result.scalars().all()
    recent_actions = [
        {
            "id": str(log.id),
            "user_id": str(log.user_id),
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": str(log.resource_id) if log.resource_id else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in recent_logs
    ]

    # Active users in last 24 hours
    day_ago = datetime.now(timezone.utc) - timedelta(hours=24)
    active_users = (await db.execute(
        select(func.count(func.distinct(AuditLog.user_id)))
        .where(AuditLog.tenant_id == tenant_id, AuditLog.created_at >= day_ago)
    )).scalar() or 0

    # Total audit entries
    total_entries = (await db.execute(
        select(func.count()).where(AuditLog.tenant_id == tenant_id)
    )).scalar() or 0

    return UserActivityResponse(
        recent_actions=recent_actions,
        active_users_24h=active_users,
        api_key_usage=0,  # Would track API key usage via middleware
        total_audit_entries=total_entries,
    )
