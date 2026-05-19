"""Artifact model."""

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Artifact(Base):
    """Artifact model."""

    __tablename__ = "artifacts"

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
    result_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("results.id", ondelete="CASCADE"),
        nullable=True,
    )
    vulnerability_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("vulnerabilities.id", ondelete="SET NULL"),
        nullable=True,
    )
    artifact_type: Mapped[str] = mapped_column(String(32), nullable=False)
    relative_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(6),
        nullable=False,
        default=datetime.utcnow,
    )

    # Relationships
    run = relationship("TaskRun", back_populates="artifacts")
    result = relationship("Result", back_populates="artifacts")
    vulnerability = relationship(
        "Vulnerability",
        back_populates="artifacts",
        foreign_keys=[vulnerability_id],
    )

    __table_args__ = (
        Index("idx_artifacts_run_id", "run_id"),
        Index("idx_artifacts_result_id", "result_id"),
        Index("idx_artifacts_vuln_id", "vulnerability_id"),
        Index("idx_artifacts_type", "artifact_type"),
    )
