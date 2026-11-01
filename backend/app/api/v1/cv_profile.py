import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.models.candidate_profile import CandidateProfile
from app.schemas.profile import ProfileRead
from app.services import cvs, profile_extraction
from app.services.llm.base import LLMClient, LLMNotConfiguredError, LLMUnavailableError
from app.services.llm.gemini import build_gemini_client
from app.services.profile_extraction import ProfileExtractionError

router = APIRouter(prefix="/cvs", tags=["cvs"])


def get_llm_client() -> LLMClient:
    """Dependency (overridden in tests: no test ever calls the real API)."""
    try:
        return build_gemini_client()
    except LLMNotConfiguredError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "L'analyse par IA n'est pas configurée sur ce serveur."
        ) from None


@router.post("/{cv_id}/profile", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
def build_profile(
    cv_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    llm: Annotated[LLMClient, Depends(get_llm_client)],
) -> CandidateProfile:
    """Build the candidate profile from the text of a CV. Creates a new profile version."""
    cv = cvs.get_cv(db, current_user.id, cv_id)
    if cv is None:  # same answer for "does not exist" and "belongs to someone else"
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CV introuvable.")
    if cv.status != "parsed" or not cv.extracted_text:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Le texte du CV n'a pas encore été extrait : lancez d'abord l'extraction.",
        )
    try:
        profile = profile_extraction.extract_profile(
            llm, cv.extracted_text, max_attempts=get_settings().llm_max_attempts
        )
    except LLMUnavailableError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Le service d'analyse est momentanément indisponible. Réessayez dans un instant.",
        ) from None
    except ProfileExtractionError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Le service d'analyse n'a pas renvoyé un profil exploitable. Réessayez.",
        ) from None
    return profile_extraction.save_llm_profile(db, cv, profile, llm)
