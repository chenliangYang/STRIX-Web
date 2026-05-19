"""Task model."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Task(Base):
    """Task model."""

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    target: Mapped[str] = mapped_column(Text, nullable=False)
    target_normalized: Mapped[str | None] = mapped_column(String(512), nullable=True)
    scan_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="standard")
    interactive: Mapped[bool] = mapped_column(default=False)
    instruction: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="not_started")
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
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
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(6), nullable=True)

    # Relationships
    creator = relationship("User", back_populates="created_tasks", foreign_keys=[created_by])
    runs = relationship("TaskRun", back_populates="task", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_tasks_created_by", "created_by"),
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_risk_level", "risk_level"),
        Index("idx_tasks_created_at", "created_at"),
        Index("idx_tasks_deleted_at", "deleted_at"),
        Index("idx_tasks_target_normalized", "target_normalized"),
    )
