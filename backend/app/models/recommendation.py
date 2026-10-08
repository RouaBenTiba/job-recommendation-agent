import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.job_offer import JobOffer
    from app.models.search import Search


class Recommendation(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        UniqueConstraint("search_id", "job_offer_id"),
        UniqueConstraint("search_id", "rank_position"),
        CheckConstraint("rank_position >= 1", name="rank_positive"),
        CheckConstraint("score >= 0 AND score <= 1", name="score_between_0_and_1"),
    )

    search_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("searches.id", ondelete="CASCADE")
    )
    job_offer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_offers.id", ondelete="RESTRICT")
    )
    rank_position: Mapped[int]
    score: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    explanation: Mapped[str] = mapped_column(Text)
    matched_skills: Mapped[list[Any]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb")
    )
    missing_skills: Mapped[list[Any]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb")
    )

    search: Mapped["Search"] = relationship(back_populates="recommendations")
    job_offer: Mapped["JobOffer"] = relationship()
