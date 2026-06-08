"""Pydantic schemas for the AI Classification endpoints."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Request Schemas ──────────────────────────────────────


class ClassifyRequest(BaseModel):
    """Request to classify a single test case."""

    test_case_id: Optional[UUID] = Field(None, description="Existing test case ID to classify")
    title: str = Field(..., min_length=1, max_length=500, description="Test case title")
    description: Optional[str] = Field(None, description="Test case description")
    steps: Optional[str] = Field(None, description="Test steps as text")


class ClassifyBatchRequest(BaseModel):
    """Request to classify multiple test cases at once."""

    test_cases: list[ClassifyRequest] = Field(
        ..., min_length=1, max_length=100, description="List of test cases to classify"
    )


class ClassificationFeedbackRequest(BaseModel):
    """Manual override / feedback on a classification result."""

    test_case_id: UUID = Field(..., description="The test case being corrected")
    dimension: str = Field(
        ...,
        pattern=r"^(business_process|criticality_level|test_case_type|dependency_class|automation_feasibility|execution_frequency)$",
        description="Which classification dimension is being corrected",
    )
    original_value: str = Field(..., description="The AI's original classification")
    corrected_value: str = Field(..., description="The human-corrected classification")
    reason: Optional[str] = Field(None, max_length=1000, description="Reason for the override")


# ── Response Schemas ─────────────────────────────────────


class ClassificationDimension(BaseModel):
    """A single classification dimension result."""

    value: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class ClassificationResponse(BaseModel):
    """Full classification result for a single test case."""

    test_case_id: Optional[UUID] = None
    business_process: ClassificationDimension
    criticality_level: ClassificationDimension
    test_case_type: ClassificationDimension
    dependency_class: ClassificationDimension
    automation_feasibility: ClassificationDimension
    execution_frequency: ClassificationDimension
    needs_review: bool = Field(..., description="True if avg confidence is below threshold")
    model_version: str
    classified_at: datetime


class ClassifyBatchResponse(BaseModel):
    """Batch classification results."""

    results: list[ClassificationResponse]
    total_classified: int
    review_required: int
    avg_confidence: float


class ClassificationFeedbackResponse(BaseModel):
    """Confirmation of a feedback/override submission."""

    id: UUID
    test_case_id: UUID
    dimension: str
    original_value: str
    corrected_value: str
    reason: Optional[str] = None
    submitted_by: UUID
    submitted_at: datetime


# ── Review Queue Schemas ─────────────────────────────────


class ReviewQueueItem(BaseModel):
    """A test case in the classification review queue."""

    test_case_id: UUID
    title: str
    classification: ClassificationResponse
    lowest_confidence_dimension: str
    lowest_confidence_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewQueueResponse(BaseModel):
    """Paginated review queue response."""

    items: list[ReviewQueueItem]
    total: int
    page: int
    page_size: int
