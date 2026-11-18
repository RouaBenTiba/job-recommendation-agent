import uuid
from typing import Any

from sqlalchemy import func, select
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


def list_profile_versions(db: Session, user_id: uuid.UUID) -> list[CandidateProfile]:
    return list(
        db.scalars(
            select(CandidateProfile)
            .where(CandidateProfile.user_id == user_id)
            .order_by(CandidateProfile.version.desc())
        )
    )


def get_profile_version(db: Session, user_id: uuid.UUID, version: int) -> CandidateProfile | None:
    return db.scalar(
        select(CandidateProfile).where(
            CandidateProfile.user_id == user_id,
            CandidateProfile.version == version,
        )
    )


def restore_profile_version(db: Session, user_id: uuid.UUID, old: CandidateProfile) -> CandidateProfile:
    """Recrée une ancienne version comme nouvelle version courante.

    L'historique n'est jamais réécrit : on ajoute une ligne, on n'en modifie aucune.
    """
    last_version = db.scalar(select(func.max(CandidateProfile.version)).where(CandidateProfile.user_id == user_id)) or 0
    current = get_current_profile(db, user_id)
    if current is not None:
        current.is_current = False
        db.flush()  # libère l'index « une seule version courante » avant l'insertion

    restored = CandidateProfile(
        user_id=user_id,
        cv_id=old.cv_id,
        version=last_version + 1,
        is_current=True,
        source="manual",
        extraction_model=old.extraction_model,
        **{field: getattr(old, field) for field in EDITABLE_FIELDS},
    )
    db.add(restored)
    db.commit()
    db.refresh(restored)
    return restored
