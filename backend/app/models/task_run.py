"""TaskRun model."""

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TaskRun(Base):
    """TaskRun model."""

    __tablename__ = "task_runs"

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
    run_no: Mapped[int] = mapped_column(Integer, nullable=False)
    scan_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    interactive: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    pid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    runner_node_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    run_dir: Mapped[str] = mapped_column(String(1024), nullable=False)
    strix_run_dir: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(6), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(6), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
    )
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
    task = relationship("Task", back_populates="runs")
    creator = relationship("User", back_populates="created_runs", foreign_keys=[created_by])
    events = relationship("RunEvent", back_populates="run", cascade="all, delete-orphan")
    result = relationship("Result", back_populates="run", uselist=False, cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("uq_task_runs_task_run_no", "task_id", "run_no", unique=True),
        Index("idx_task_runs_task_id", "task_id"),
        Index("idx_task_runs_status", "status"),
        Index("idx_task_runs_created_at", "created_at"),
        Index("idx_task_runs_started_at", "started_at"),
    )
