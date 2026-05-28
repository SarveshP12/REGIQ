"""Change Set & Change Component models — parsed ServiceNow update sets."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ChangeSet(Base):
    __tablename__ = "change_sets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    release_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("releases.id"), nullable=True, index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="servicenow")  # servicenow, manual
    update_set_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    component_count: Mapped[int] = mapped_column(Integer, default=0)
    analysis_status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    impact_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    release = relationship("Release", back_populates="change_sets", lazy="selectin")
    components = relationship("ChangeComponent", back_populates="change_set", lazy="selectin")


class ChangeComponent(Base):
    __tablename__ = "change_components"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    change_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("change_sets.id"), nullable=False, index=True
    )
    component_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    component_name: Mapped[str] = mapped_column(String(500), nullable=False)
    scope: Mapped[str | None] = mapped_column(String(255), nullable=True)
    table_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    change_type: Mapped[str] = mapped_column(String(50), default="modified")  # created, modified, deleted
    raw_diff: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    attributes: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    change_set = relationship("ChangeSet", back_populates="components", lazy="selectin")
