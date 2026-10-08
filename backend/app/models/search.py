import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.recommendation import Recommendation
    from app.models.user import User


class Search(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "searches"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="status_valid",
        ),
        CheckConstraint("iterations_count >= 0", name="iterations_non_negative"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    profile_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="SET NULL"))
    objective: Mapped[str] = mapped_column(Text)
    filters: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    status: Mapped[str] = mapped_column(String(20), server_default="pending")
    iterations_count: Mapped[int] = mapped_column(server_default=text("0"))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="searches")
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="search",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Recommendation.rank_position",
    )
