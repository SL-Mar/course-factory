"""SQLAlchemy 2.0 declarative models for Course Factory."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(timezone.utc)


def _new_uuid() -> uuid.UUID:
    """Generate a new UUID4."""
    return uuid.uuid4()


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    type_annotation_map = {
        dict[str, Any]: JSON,
    }


class Course(Base):
    """A course project tracked through the generation pipeline."""

    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=_new_uuid
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="draft")
    source_urls: Mapped[list[Any]] = mapped_column(JSON, default=list)
    target_platform: Mapped[str] = mapped_column(String(50), default="udemy")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict
    )

    # Relationships
    pipeline_runs: Mapped[list["PipelineRun"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )
    knowledge_chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Course(id={self.id!s}, title={self.title!r}, status={self.status!r})>"


class PipelineRun(Base):
    """A single pipeline stage execution record."""

    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=_new_uuid
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE")
    )
    stage: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    checkpoint_data: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="pipeline_runs")

    def __repr__(self) -> str:
        return (
            f"<PipelineRun(id={self.id!s}, stage={self.stage!r}, "
            f"status={self.status!r})>"
        )


class KnowledgeChunk(Base):
    """A chunk of extracted knowledge from a source document."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=_new_uuid
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE")
    )
    source_type: Mapped[str] = mapped_column(String(50))
    source_url: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    embedding_id: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="knowledge_chunks")

    def __repr__(self) -> str:
        return (
            f"<KnowledgeChunk(id={self.id!s}, source_type={self.source_type!r}, "
            f"chunk_index={self.chunk_index})>"
        )


class Customer(Base):
    """A licensed customer of Course Factory."""

    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=_new_uuid
    )
    email: Mapped[str] = mapped_column(String(255), unique=True)
    license_key: Mapped[str] = mapped_column(String(500))
    tier: Mapped[str] = mapped_column(String(20), default="free")
    product: Mapped[str] = mapped_column(String(10))
    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    max_machines: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    def __repr__(self) -> str:
        return (
            f"<Customer(id={self.id!s}, email={self.email!r}, "
            f"tier={self.tier!r})>"
        )
