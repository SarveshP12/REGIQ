"""Pydantic schemas for Test Case endpoints."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Create / Update ────────────────────────────────────────


class TestCaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    steps: Optional[list[dict[str, Any]]] = []
    preconditions: Optional[str] = None
    expected_results: Optional[str] = None
    format_type: str = Field("structured", pattern=r"^(structured|bdd|freeform)$")
    status: str = "draft"
    criticality: str = "medium"
    type_tags: Optional[list[str]] = []
    automation_flag: str = "manual"
    business_process_id: Optional[UUID] = None
    traceability: Optional[dict[str, Any]] = {}


class TestCaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    steps: Optional[list[dict[str, Any]]] = None
    preconditions: Optional[str] = None
    expected_results: Optional[str] = None
    format_type: Optional[str] = None
    status: Optional[str] = None
    criticality: Optional[str] = None
    type_tags: Optional[list[str]] = None
    automation_flag: Optional[str] = None
    business_process_id: Optional[UUID] = None
    traceability: Optional[dict[str, Any]] = None


# ── Response ──────────────────────────────────────────────


class TestCaseResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    steps: Optional[list[dict[str, Any]]] = []
    preconditions: Optional[str] = None
    expected_results: Optional[str] = None
    format_type: str
    status: str
    criticality: str
    type_tags: Optional[list[str]] = []
    automation_flag: str
    business_process_id: Optional[UUID] = None
    tenant_id: UUID
    created_by: Optional[UUID] = None
    traceability: Optional[dict[str, Any]] = {}
    version: int
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TestCaseListResponse(BaseModel):
    items: list[TestCaseResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ── Import / Export ───────────────────────────────────────


class ImportPreviewRow(BaseModel):
    row_number: int
    title: str
    status: str = "valid"
    errors: list[str] = []
    data: dict[str, Any] = {}


class ImportResult(BaseModel):
    total_rows: int
    imported: int
    skipped: int
    errors: list[dict[str, Any]] = []


# ── Version ───────────────────────────────────────────────


class TestCaseVersionResponse(BaseModel):
    version: int
    changed_fields: list[str]
    changed_by: Optional[UUID] = None
    timestamp: datetime
    snapshot: dict[str, Any]


class DuplicateCheckRequest(BaseModel):
    title: str
    description: Optional[str] = None
