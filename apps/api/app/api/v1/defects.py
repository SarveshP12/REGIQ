"""Defect endpoints — /api/v1/defects.

Provides:
  - POST /import          — Import defects from external systems (Jira, ADO, ServiceNow)
  - GET  /                — List defects with filtering and pagination
  - GET  /{id}            — Get defect details
  - POST /link            — Link defect to test case / component
  - GET  /stats           — Defect intelligence summary statistics
"""

import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit
from app.core.database import get_db
from app.core.security import get_current_user, require_permissions
from app.models.defect import Defect
from app.models.user import User
from app.schemas.defect import (
    DefectImportRequest,
    DefectImportResult,
    DefectLinkRequest,
    DefectListResponse,
    DefectResponse,
    DefectStatsResponse,
)

router = APIRouter()


# ── Import from External Systems ─────────────────────────


@router.post(
    "/import",
    response_model=DefectImportResult,
    dependencies=[Depends(require_permissions("tests:write"))],
)
async def import_defects(
    body: DefectImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import defects from an external system (Jira, Azure DevOps, or ServiceNow)."""
    config = body.config or {}
    defects_data = []

    if body.source == "jira":
        from app.services.jira_client import jira_client

        jql = config.get("jql", "type = Bug ORDER BY created DESC")
        defects_data = await jira_client.fetch_defects(jql=jql)

    elif body.source == "ado":
        from app.services.ado_client import AzureDevOpsClient

        ado = AzureDevOpsClient(
            organization=config.get("organization", "regiq-org"),
            project=config.get("project", "REGIQ"),
            pat=config.get("pat", "mock_pat"),
        )
        defects_data = await ado.fetch_defects(
            area_path=config.get("area_path"),
            iteration_path=config.get("iteration_path"),
        )

    elif body.source == "servicenow":
        from app.services.servicenow_defect_client import ServiceNowDefectClient

        sn = ServiceNowDefectClient(
            instance_url=config.get("instance_url", "https://dev.service-now.com"),
            client_id=config.get("client_id", ""),
            client_secret_encrypted=config.get("client_secret_encrypted", ""),
        )
        defects_data = await sn.fetch_defects()

    imported = 0
    updated = 0
    errors = []

    for data in defects_data:
        try:
            stmt = select(Defect).where(
                Defect.external_id == data["external_id"],
                Defect.source_system == data["source_system"],
                Defect.tenant_id == current_user.tenant_id,
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.status = data.get("status", existing.status)
                existing.severity = data.get("severity", existing.severity)
                existing.title = data.get("title", existing.title)
                existing.module = data.get("module", existing.module)
                updated += 1
            else:
                # Check for repeat defects (same title, different external_id)
                title_check = await db.execute(
                    select(func.count()).where(
                        Defect.title == data["title"],
                        Defect.tenant_id == current_user.tenant_id,
                    )
                )
                is_repeat = (title_check.scalar() or 0) > 0

                new_defect = Defect(
                    external_id=data["external_id"],
                    title=data["title"],
                    severity=data.get("severity", "Medium"),
                    status=data.get("status", "Open"),
                    module=data.get("module"),
                    source_system=data["source_system"],
                    tenant_id=current_user.tenant_id,
                    is_repeat=is_repeat,
                    recurrence_count=1 if is_repeat else 0,
                )
                db.add(new_defect)
                imported += 1
        except Exception as e:
            errors.append(f"Error processing {data.get('external_id', '?')}: {str(e)}")

    await db.flush()

    await log_audit(
        db, current_user.id, "defect_import", "defect",
        tenant_id=current_user.tenant_id,
        details={"source": body.source, "imported": imported, "updated": updated},
    )

    return DefectImportResult(
        source=body.source,
        total_fetched=len(defects_data),
        imported=imported,
        updated=updated,
        errors=errors,
    )


# ── List Defects ─────────────────────────────────────────


@router.get(
    "/",
    response_model=DefectListResponse,
    dependencies=[Depends(require_permissions("tests:read"))],
)
async def list_defects(
    module: Optional[str] = Query(None, description="Filter by module"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source system"),
    search: Optional[str] = Query(None, description="Search title"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List defects with filtering and pagination."""
    base = select(Defect).where(Defect.tenant_id == current_user.tenant_id)

    if module:
        base = base.where(Defect.module == module)
    if severity:
        base = base.where(Defect.severity == severity)
    if status:
        base = base.where(Defect.status == status)
    if source:
        base = base.where(Defect.source_system == source)
    if search:
        base = base.where(Defect.title.ilike(f"%{search}%"))

    # Count total
    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = base.order_by(Defect.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    defects = result.scalars().all()

    return DefectListResponse(
        items=[DefectResponse.model_validate(d) for d in defects],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── Get Defect Detail ────────────────────────────────────


@router.get(
    "/{defect_id}",
    response_model=DefectResponse,
    dependencies=[Depends(require_permissions("tests:read"))],
)
async def get_defect(
    defect_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single defect by ID."""
    result = await db.execute(
        select(Defect).where(
            Defect.id == defect_id,
            Defect.tenant_id == current_user.tenant_id,
        )
    )
    defect = result.scalar_one_or_none()
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")
    return DefectResponse.model_validate(defect)


# ── Link Defect ──────────────────────────────────────────


@router.post(
    "/link",
    dependencies=[Depends(require_permissions("tests:write"))],
)
async def link_defect(
    body: DefectLinkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Link a defect to a test case and/or component."""
    result = await db.execute(
        select(Defect).where(
            Defect.id == body.defect_id,
            Defect.tenant_id == current_user.tenant_id,
        )
    )
    defect = result.scalar_one_or_none()
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")

    if body.test_case_id:
        defect.test_case_id = body.test_case_id
    if body.component_id:
        defect.component_id = body.component_id

    await db.flush()

    await log_audit(
        db, current_user.id, "defect_link", "defect",
        resource_id=defect.id,
        tenant_id=current_user.tenant_id,
        details={
            "test_case_id": str(body.test_case_id) if body.test_case_id else None,
            "component_id": str(body.component_id) if body.component_id else None,
        },
    )

    return {"status": "linked", "defect_id": str(defect.id)}


# ── Defect Statistics ────────────────────────────────────


@router.get(
    "/stats/summary",
    response_model=DefectStatsResponse,
    dependencies=[Depends(require_permissions("dashboards:read"))],
)
async def defect_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Defect intelligence summary statistics."""
    tenant_id = current_user.tenant_id
    base = Defect.tenant_id == tenant_id

    total = (await db.execute(select(func.count()).where(base))).scalar() or 0

    # Severity distribution
    sev_q = await db.execute(
        select(Defect.severity, func.count())
        .where(base)
        .group_by(Defect.severity)
    )
    severity_dist = {row[0]: row[1] for row in sev_q.all()}

    # Module distribution
    mod_q = await db.execute(
        select(Defect.module, func.count())
        .where(base, Defect.module.isnot(None))
        .group_by(Defect.module)
    )
    module_dist = {row[0]: row[1] for row in mod_q.all()}

    # Status distribution
    status_q = await db.execute(
        select(Defect.status, func.count())
        .where(base)
        .group_by(Defect.status)
    )
    status_dist = {row[0]: row[1] for row in status_q.all()}

    # Repeat defects
    repeat_count = (await db.execute(
        select(func.count()).where(base, Defect.is_repeat.is_(True))
    )).scalar() or 0

    # Source distribution
    src_q = await db.execute(
        select(Defect.source_system, func.count())
        .where(base)
        .group_by(Defect.source_system)
    )
    sources = {row[0]: row[1] for row in src_q.all()}

    return DefectStatsResponse(
        total_defects=total,
        severity_distribution=severity_dist,
        module_distribution=module_dist,
        status_distribution=status_dist,
        repeat_defect_count=repeat_count,
        repeat_defect_rate=round(repeat_count / max(total, 1), 3),
        sources=sources,
    )
