"""Pydantic schemas for dashboard / reporting endpoints."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class RepositoryHealthResponse(BaseModel):
    total_test_cases: int
    status_distribution: dict[str, int]
    criticality_breakdown: dict[str, int]
    unmapped_tests: int  # tests without business_process_id
    stale_test_count: int  # tests not updated in 90+ days
    automation_breakdown: dict[str, int]
    format_distribution: dict[str, int]
    recent_additions: int  # last 7 days


class SyncStatusDashboard(BaseModel):
    connections: list[dict[str, Any]]
    total_change_sets: int
    pending_analysis: int
    total_components: int
    last_sync_time: Optional[datetime] = None
    error_count: int


class UserActivityResponse(BaseModel):
    recent_actions: list[dict[str, Any]]
    active_users_24h: int
    api_key_usage: int
    total_audit_entries: int
