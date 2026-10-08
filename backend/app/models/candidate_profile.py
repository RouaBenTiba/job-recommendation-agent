import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class CandidateProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "candidate_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", "version"),
        # Une seule version courante par utilisatrice
        Index(
            "uq_candidate_profiles_current_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("is_current"),
        ),
        CheckConstraint("version >= 1", name="version_positive"),
        CheckConstraint("source IN ('llm', 'manual')", name="source_valid"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    cv_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cvs.id", ondelete="SET NULL"))
    version: Mapped[int]
    is_current: Mapped[bool] = mapped_column(server_default=text("true"))
    summary: Mapped[str | None] = mapped_column(Text)
    education: Mapped[list[Any]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    experiences: Mapped[list[Any]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    skills: Mapped[list[Any]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    technologies: Mapped[list[Any]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    interests: Mapped[list[Any]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    objectives: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(10), server_default="llm")
    extraction_model: Mapped[str | None] = mapped_column(String(100))

    user: Mapped["User"] = relationship(back_populates="profiles")
