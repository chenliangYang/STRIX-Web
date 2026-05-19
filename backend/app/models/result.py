"""Result model."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Result(Base):
    """Result model."""

    __tablename__ = "results"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id"),
        nullable=False,
    )
    run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("task_runs.id"),
        nullable=False,
        unique=True,
    )
    project_name: Mapped[str] = mapped_column(String(128), nullable=False)
    target: Mapped[str] = mapped_column(Text, nullable=False)
    scan_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    interactive: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    vulnerability_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    artifact_dir: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(6), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(6),
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(6),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    task = relationship("Task", back_populates="results")
    run = relationship("TaskRun", back_populates="result")
    vulnerabilities = relationship("Vulnerability", back_populates="result", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="result", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_results_task_id", "task_id"),
        Index("idx_results_status", "status"),
        Index("idx_results_risk_level", "risk_level"),
        Index("idx_results_started_at", "started_at"),
    )
