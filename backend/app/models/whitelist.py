"""Whitelist model."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Whitelist(Base):
    """Whitelist model."""

    __tablename__ = "whitelists"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_value: Mapped[str] = mapped_column(Text, nullable=False)
    target_normalized: Mapped[str] = mapped_column(String(512), nullable=False)
    project: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="enabled")
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
    creator = relationship("User", back_populates="created_whitelists", foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_whitelists_type", "target_type"),
        Index("idx_whitelists_status", "status"),
        Index("idx_whitelists_target_normalized", "target_normalized"),
    )
