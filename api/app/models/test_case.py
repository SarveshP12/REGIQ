"""Test Case model — the central entity of the REGIQ platform."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    steps: Mapped[dict | None] = mapped_column(JSONB, default=list)
    preconditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_results: Mapped[str | None] = mapped_column(Text, nullable=True)
    format_type: Mapped[str] = mapped_column(String(50), default="structured")  # structured, bdd, freeform

    # Classification
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    criticality: Mapped[str] = mapped_column(String(50), default="medium", index=True)
    type_tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=list)
    automation_flag: Mapped[str] = mapped_column(String(50), default="manual")  # manual, automated, hybrid

    # Relations
    business_process_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business_processes.id"), nullable=True, index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # AI / Embedding (populated in Phase 2)
    embedding_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criticality_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Full-text search vector
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    business_process = relationship("BusinessProcess", back_populates="test_cases", lazy="selectin")
