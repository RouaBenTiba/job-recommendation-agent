import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class CV(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cvs"
    __table_args__ = (
        CheckConstraint("file_size_bytes > 0", name="file_size_positive"),
        CheckConstraint("status IN ('uploaded', 'parsed', 'failed')", name="status_valid"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100), server_default="application/pdf")
    file_size_bytes: Mapped[int]
    storage_path: Mapped[str] = mapped_column(String(500))
    extracted_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), server_default="uploaded")
    error_message: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="cvs")
