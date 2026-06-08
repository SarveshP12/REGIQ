"""Pydantic schemas for Defect endpoints."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Import Request ───────────────────────────────────────


class DefectImportRequest(BaseModel):
    """Request to import defects from an external source."""

    source: str = Field(
        ...,
        pattern=r"^(jira|ado|servicenow)$",
        description="Source system: jira, ado, or servicenow",
    )
    config: Optional[dict[str, Any]] = Field(
        None,
        description="Source-specific config (e.g. JQL for Jira, project for ADO, filter for ServiceNow)",
    )


class DefectLinkRequest(BaseModel):
    """Link a defect to a test case and/or component."""

    defect_id: UUID
    test_case_id: Optional[UUID] = None
    component_id: Optional[UUID] = None


# ── Responses ────────────────────────────────────────────


class DefectResponse(BaseModel):
    id: UUID
    external_id: str
    source_system: str
    title: str
    description: Optional[str] = None
    severity: str
    module: Optional[str] = None
    status: str
    recurrence_count: int
    is_repeat: bool
    component_id: Optional[UUID] = None
    test_case_id: Optional[UUID] = None
    release_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DefectListResponse(BaseModel):
    items: list[DefectResponse]
    total: int
    page: int
    page_size: int


class DefectImportResult(BaseModel):
    source: str
    total_fetched: int
    imported: int
    updated: int
    errors: list[str] = []


class DefectStatsResponse(BaseModel):
    """Defect intelligence summary statistics."""

    total_defects: int
    severity_distribution: dict[str, int]
    module_distribution: dict[str, int]
    status_distribution: dict[str, int]
    repeat_defect_count: int
    repeat_defect_rate: float
    sources: dict[str, int]
