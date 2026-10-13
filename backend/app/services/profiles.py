import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile
from app.schemas.profile import ProfileUpdate

EDITABLE_FIELDS = (
    "summary",
    "objectives",
    "education",
    "experiences",
    "skills",
    "technologies",
    "interests",
)
NULLABLE_FIELDS = {"summary", "objectives"}


def get_current_profile(db: Session, user_id: uuid.UUID) -> CandidateProfile | None:
    return db.scalar(
        select(CandidateProfile).where(
            CandidateProfile.user_id == user_id,
            CandidateProfile.is_current.is_(True),
        )
    )


def update_profile(db: Session, user_id: uuid.UUID, data: ProfileUpdate) -> CandidateProfile:
    changes: dict[str, Any] = data.model_dump(mode="json", exclude_unset=True)
    # Les colonnes de liste sont NOT NULL : un « null » envoyé est ignoré.
    changes = {key: value for key, value in changes.items() if value is not None or key in NULLABLE_FIELDS}

    current = get_current_profile(db, user_id)
    if current is None:
        profile = CandidateProfile(user_id=user_id, version=1, is_current=True, source="manual", **changes)
    else:
        values = {field: getattr(current, field) for field in EDITABLE_FIELDS}
        values.update(changes)
        current.is_current = False
        db.flush()  # libère l'index « une seule version courante » avant l'insertion
        profile = CandidateProfile(
            user_id=user_id,
            cv_id=current.cv_id,
            version=current.version + 1,
            is_current=True,
            source="manual",
            extraction_model=current.extraction_model,
            **values,
        )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
