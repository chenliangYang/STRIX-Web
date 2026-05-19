"""RunEvent model."""

import uuid
from datetime import datetime

from sqlalchemy import String, BigInteger, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RunEvent(Base):
    """RunEvent model."""

    __tablename__ = "run_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("task_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    seq: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    event_time: Mapped[datetime | None] = mapped_column(DateTime(6), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    source_file: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_offset: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(6),
        nullable=False,
        default=datetime.utcnow,
    )

    # Relationships
    run = relationship("TaskRun", back_populates="events")

    __table_args__ = (
        Index("uq_run_events_run_seq", "run_id", "seq", unique=True),
        Index("idx_run_events_run_seq", "run_id", "seq"),
        Index("idx_run_events_type", "event_type"),
        Index("idx_run_events_created_at", "created_at"),
    )
