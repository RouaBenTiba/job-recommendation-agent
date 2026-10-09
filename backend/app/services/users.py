"""User persistence. The only module that touches User columns (adapt here)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == normalize_email(email)))


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def create_user(db: Session, email: str, password: str, full_name: str | None = None) -> User:
    user = User(
        email=normalize_email(email),
        password_hash=hash_password(password),
        full_name=full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def mark_logged_in(db: Session, user: User) -> None:
    user.last_login_at = datetime.now(UTC)
    db.commit()
