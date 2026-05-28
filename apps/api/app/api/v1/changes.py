"""Change parsing and history endpoints — /api/v1/changes."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit
from app.core.database import get_db
from app.core.mongodb import get_mongo_db
from app.core.security import get_current_user, require_permissions
from app.models.change_set import ChangeComponent, ChangeSet
from app.models.user import User
from app.schemas.servicenow import (
    ChangeComponentResponse,
    ChangeHistoryResponse,
    ChangeManifestResponse,
    ParseUpdateSetRequest,
)
from app.services.update_set_parser import parse_update_set_xml

router = APIRouter()


# ── Parse update set XML ──────────────────────────────────


@router.post(
    "/parse",
    response_model=ChangeManifestResponse,
    status_code=201,
    dependencies=[Depends(require_permissions("changes:write"))],
)
async def parse_update_set(
    body: ParseUpdateSetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Parse a ServiceNow update-set XML and store the components."""
    # Parse XML
    components = parse_update_set_xml(body.xml_content)

    # Create ChangeSet record
    cs = ChangeSet(
        name=body.change_set_name,
        release_id=body.release_id,
        tenant_id=current_user.tenant_id,
        source_type="servicenow",
        component_count=len(components),
        analysis_status="completed",
        impact_count=len(components),
    )
    db.add(cs)
    await db.flush()

    # Store raw XML in MongoDB
    mongo = get_mongo_db()
    await mongo.update_set_raw.insert_one({
        "change_set_id": str(cs.id),
        "raw_xml": body.xml_content[:500_000],  # cap storage
        "parsed_components": components,
        "metadata": {"parser_version": "1.0", "component_count": len(components)},
        "tenant_id": str(current_user.tenant_id),
        "created_at": datetime.now(timezone.utc),
    })

    # Create ChangeComponent records in PostgreSQL
    db_components = []
    for comp in components:
        cc = ChangeComponent(
            change_set_id=cs.id,
            component_type=comp["component_type"],
            component_name=comp["component_name"],
            scope=comp.get("scope"),
            table_name=comp.get("table_name"),
            change_type=comp.get("change_type", "modified"),
            attributes=comp.get("attributes", {}),
        )
        db.add(cc)
        db_components.append(cc)

    await db.flush()

    await log_audit(
        db, current_user.id, "parse", "change_set",
        resource_id=cs.id, tenant_id=current_user.tenant_id,
        details={"component_count": len(components)},
    )

    return ChangeManifestResponse(
        id=cs.id,
        name=cs.name,
        source_type=cs.source_type,
        component_count=cs.component_count,
        analysis_status=cs.analysis_status,
        components=[ChangeComponentResponse.model_validate(c) for c in db_components],
        created_at=cs.created_at,
    )


# ── Get parsed change manifest ────────────────────────────


@router.get(
    "/{change_set_id}/manifest",
    response_model=ChangeManifestResponse,
    dependencies=[Depends(require_permissions("changes:read"))],
)
async def get_manifest(
    change_set_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the parsed change manifest for a specific change set."""
    result = await db.execute(
        select(ChangeSet).where(
            ChangeSet.id == change_set_id,
            ChangeSet.tenant_id == current_user.tenant_id,
        )
    )
    cs = result.scalar_one_or_none()
    if not cs:
        raise HTTPException(status_code=404, detail="Change set not found")

    comp_result = await db.execute(
        select(ChangeComponent).where(ChangeComponent.change_set_id == change_set_id)
    )
    components = comp_result.scalars().all()

    return ChangeManifestResponse(
        id=cs.id,
        name=cs.name,
        source_type=cs.source_type,
        component_count=cs.component_count,
        analysis_status=cs.analysis_status,
        components=[ChangeComponentResponse.model_validate(c) for c in components],
        created_at=cs.created_at,
    )


# ── Change history ────────────────────────────────────────


@router.get(
    "/history",
    response_model=ChangeHistoryResponse,
    dependencies=[Depends(require_permissions("changes:read"))],
)
async def change_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get change set history with pagination."""
    query = select(ChangeSet).where(ChangeSet.tenant_id == current_user.tenant_id)

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(ChangeSet.created_at.desc()).offset(offset).limit(page_size)
    )
    change_sets = result.scalars().all()

    items = []
    for cs in change_sets:
        comp_result = await db.execute(
            select(ChangeComponent).where(ChangeComponent.change_set_id == cs.id)
        )
        components = comp_result.scalars().all()
        items.append(ChangeManifestResponse(
            id=cs.id,
            name=cs.name,
            source_type=cs.source_type,
            component_count=cs.component_count,
            analysis_status=cs.analysis_status,
            components=[ChangeComponentResponse.model_validate(c) for c in components],
            created_at=cs.created_at,
        ))

    return ChangeHistoryResponse(items=items, total=total)
