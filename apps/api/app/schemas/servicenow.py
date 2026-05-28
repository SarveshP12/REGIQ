"""Pydantic schemas for ServiceNow integration endpoints."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Connection ────────────────────────────────────────────


class ServiceNowConnect(BaseModel):
    instance_url: str = Field(..., description="ServiceNow instance URL, e.g. https://dev12345.service-now.com")
    client_id: str
    client_secret: str
    environment: str = Field("dev", pattern=r"^(dev|test|uat|prod)$")
    name: str = Field(..., min_length=1, max_length=255, description="Friendly name for this connection")


class ServiceNowConnectionResponse(BaseModel):
    id: UUID
    name: str
    instance_url: str
    environment: str
    status: str
    last_sync_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Sync ──────────────────────────────────────────────────


class SyncTrigger(BaseModel):
    connection_id: UUID
    sync_type: str = Field("delta", pattern=r"^(delta|full)$")


class SyncStatusResponse(BaseModel):
    connection_id: UUID
    sync_type: str
    status: str  # running, completed, failed
    started_at: datetime
    completed_at: Optional[datetime] = None
    components_synced: int = 0
    errors: list[str] = []


# ── Integration Health ────────────────────────────────────


class IntegrationHealthResponse(BaseModel):
    connections: list[dict[str, Any]]
    overall_status: str  # healthy, degraded, unhealthy
    last_check: datetime


# ── Change Parsing ────────────────────────────────────────


class ParseUpdateSetRequest(BaseModel):
    """Submit raw update-set XML for parsing."""
    xml_content: str = Field(..., description="Raw update set XML")
    change_set_name: str = Field(..., min_length=1, max_length=500)
    release_id: Optional[UUID] = None


class ChangeComponentResponse(BaseModel):
    id: UUID
    component_type: str
    component_name: str
    scope: Optional[str] = None
    table_name: Optional[str] = None
    change_type: str
    attributes: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChangeManifestResponse(BaseModel):
    id: UUID
    name: str
    source_type: str
    component_count: int
    analysis_status: str
    components: list[ChangeComponentResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChangeHistoryResponse(BaseModel):
    items: list[ChangeManifestResponse]
    total: int
