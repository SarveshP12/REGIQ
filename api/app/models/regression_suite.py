"""Regression Suite & Suite Test Case junction models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RegressionSuite(Base):
    __tablename__ = "regression_suites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    release_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("releases.id"), nullable=True, index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    strategy_type: Mapped[str] = mapped_column(String(50), default="standard")
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    total_tests: Mapped[int] = mapped_column(Integer, default=0)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    coverage_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    generated_by: Mapped[str] = mapped_column(String(50), default="manual")  # manual, ai
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    release = relationship("Release", back_populates="regression_suites", lazy="selectin")
    suite_tests = relationship("SuiteTestCase", back_populates="suite", lazy="selectin")


class SuiteTestCase(Base):
    __tablename__ = "suite_test_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suite_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regression_suites.id"), nullable=False, index=True
    )
    test_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_cases.id"), nullable=False, index=True
    )
    inclusion_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    execution_status: Mapped[str] = mapped_column(String(50), default="pending")
    result: Mapped[str | None] = mapped_column(String(50), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    suite = relationship("RegressionSuite", back_populates="suite_tests", lazy="selectin")
