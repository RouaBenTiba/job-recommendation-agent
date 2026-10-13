import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.preference import Preference
from app.schemas.preference import PreferencesUpdate


def get_preferences(db: Session, user_id: uuid.UUID) -> Preference | None:
    return db.scalar(select(Preference).where(Preference.user_id == user_id))


def upsert_preferences(db: Session, user_id: uuid.UUID, data: PreferencesUpdate) -> Preference:
    preferences = get_preferences(db, user_id)
    if preferences is None:
        preferences = Preference(user_id=user_id)
        db.add(preferences)
    for field, value in data.model_dump().items():
        setattr(preferences, field, value)
    db.commit()
    db.refresh(preferences)
    return preferences
