from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user  # ADAPTER : nom exact dans deps.py
from app.db.session import get_db
from app.models.candidate_profile import CandidateProfile
from app.models.user import User
from app.schemas.profile import ProfileRead, ProfileUpdate
from app.services.profiles import get_current_profile, update_profile

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


@router.patch("", response_model=ProfileRead)
def patch_profile(
    data: ProfileUpdate, current_user: CurrentUser, db: DbSession
) -> CandidateProfile:
    return update_profile(db, current_user.id, data)