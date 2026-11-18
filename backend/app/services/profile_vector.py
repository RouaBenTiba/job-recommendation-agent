"""Point d'accroche pour recalculer le vecteur d'un profil (US-4.4, tâche 4).

Le vrai calcul (embeddings + base vectorielle) arrive avec l'EPIC-5. En attendant,
le recalcul ne fait rien, mais il est déjà appelé après chaque changement du profil.
"""

import logging
from typing import Protocol

from app.models.candidate_profile import CandidateProfile
from app.services.profile_text import profile_text_hash, profile_to_text

logger = logging.getLogger(__name__)


class ProfileVectorizer(Protocol):
    def refresh(self, profile: CandidateProfile, text: str) -> None:
        """Calcule et enregistre le vecteur du profil à partir de son texte."""


class NoopProfileVectorizer:
    def refresh(self, profile: CandidateProfile, text: str) -> None:
        logger.debug("Vecteur du profil non calculé (EPIC-5 pas encore branché)")


_vectorizer: ProfileVectorizer = NoopProfileVectorizer()


def set_profile_vectorizer(vectorizer: ProfileVectorizer) -> None:
    """Choisit l'implémentation (l'EPIC-5 y mettra l'embedding et ChromaDB)."""
    global _vectorizer
    _vectorizer = vectorizer


def refresh_profile_vector(profile: CandidateProfile) -> None:
    """Recalcule le vecteur après une modification, sans bloquer la requête."""
    try:
        text = profile_to_text(profile)
        if not text:
            return
        logger.debug("Empreinte du profil : %s", profile_text_hash(text)[:12])
        _vectorizer.refresh(profile, text)
    except Exception as exc:  # un échec du vecteur ne doit pas bloquer la candidate
        logger.warning("Vecteur du profil non recalculé (%s)", type(exc).__name__)
