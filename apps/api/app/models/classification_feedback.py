"""Classification Feedback model — stores human corrections to AI classifications.

Each record represents a single dimension override. These records serve a dual
purpose: (1) immediate manual correction of the classification on the test case,
and (2) training data for the next model retraining cycle.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ClassificationFeedback(Base):
    __tablename__ = "classification_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    test_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_cases.id"), nullable=False, index=True
    )
    dimension: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="business_process | criticality_level | test_case_type | dependency_class | automation_feasibility | execution_frequency",
    )
    original_value: Mapped[str] = mapped_column(String(255), nullable=False)
    corrected_value: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Who submitted the correction
    submitted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    # Model version that produced the original classification
    model_version: Mapped[str] = mapped_column(String(100), nullable=False, default="rule-based-v1")

    # Whether this feedback has been consumed by a retraining job
    consumed_for_training: Mapped[bool] = mapped_column(default=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
