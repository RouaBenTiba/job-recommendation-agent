from datetime import datetime
from typing import Any

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    DateTime,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class JobOffer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_offers"
    __table_args__ = (
        UniqueConstraint("source", "external_id"),
        CheckConstraint("source IN ('adzuna', 'jooble', 'web')", name="source_valid"),
        CheckConstraint(
            "contract_type IN ('internship', 'apprenticeship', 'full_time', " "'part_time', 'contract', 'other')",
            name="contract_type_valid",
        ),
        CheckConstraint("status IN ('active', 'expired')", name="status_valid"),
    )

    source: Mapped[str] = mapped_column(String(20))
    external_id: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(CHAR(2))
    contract_type: Mapped[str | None] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text)
    required_skills: Mapped[list[Any]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    url: Mapped[str] = mapped_column(String(1000))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(10), server_default="active")
    content_hash: Mapped[str] = mapped_column(CHAR(64), unique=True)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
