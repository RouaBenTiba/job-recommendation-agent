from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.api.deps import get_current_user  # ADAPTER : nom exact dans deps.py
from app.db.session import get_db
from app.models.candidate_profile import CandidateProfile
from app.models.user import User
from app.schemas.profile import ProfileRead, ProfileUpdate, ProfileVersionRead
from app.services.profiles import (
    get_current_profile,
    get_profile_version,
    list_profile_versions,
    restore_profile_version,
    update_profile,
)
from app.services.profile_vector import refresh_profile_vector
router = APIRouter(prefix="/profile", tags=["profile"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=ProfileRead)
def read_profile(current_user: CurrentUser, db: DbSession) -> CandidateProfile:
    profile = get_current_profile(db, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Aucun profil pour le moment : importez un CV ou renseignez-le.",
        )
    return profile


VersionNumber = Annotated[int, Path(ge=1, description="Numéro de version du profil")]


@router.patch("", response_model=ProfileRead)
def patch_profile(data: ProfileUpdate, current_user: CurrentUser, db: DbSession) -> CandidateProfile:
    profile = update_profile(db, current_user.id, data)
    refresh_profile_vector(profile)
    return profile


@router.get("/versions", response_model=list[ProfileVersionRead])
def list_versions(current_user: CurrentUser, db: DbSession) -> list[CandidateProfile]:
    return list_profile_versions(db, current_user.id)


@router.get("/versions/{version}", response_model=ProfileRead)
def read_version(version: VersionNumber, current_user: CurrentUser, db: DbSession) -> CandidateProfile:
    profile = get_profile_version(db, current_user.id, version)
    if profile is None:
        raise HTTPException(status_code=404, detail="Version du profil introuvable.")
    return profile


@router.post("/versions/{version}/restore", response_model=ProfileRead, status_code=201)
def restore_version(version: VersionNumber, current_user: CurrentUser, db: DbSession) -> CandidateProfile:
    old = get_profile_version(db, current_user.id, version)
    if old is None:
        raise HTTPException(status_code=404, detail="Version du profil introuvable.")
    if old.is_current:
        raise HTTPException(status_code=409, detail="Cette version est déjà la version courante.")
    profile = restore_profile_version(db, current_user.id, old)
    refresh_profile_vector(profile)
    return profile
