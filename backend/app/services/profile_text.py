"""Texte qui représente un profil, pour calculer son vecteur (US-4.4, tâche 4)."""

import hashlib
from typing import Any

from app.models.candidate_profile import CandidateProfile

# Les modèles d'embeddings acceptent un texte de taille bornée.
MAX_PROFILE_TEXT_CHARS = 6000


def _clean(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _join(values: list[Any] | None) -> str:
    return ", ".join(text for text in (_clean(value) for value in values or []) if text)


def _period(start: Any, end: Any) -> str:
    first, last = _clean(start), _clean(end)
    if first and last:
        return f"{first} - {last}"
    return first or last


def _experience_line(item: dict[str, Any]) -> str:
    title, company = _clean(item.get("title")), _clean(item.get("company"))
    head = " chez ".join(part for part in (title, company) if part)
    period = _period(item.get("start"), item.get("end"))
    line = f"- {head}" + (f" ({period})" if period else "")
    description = _clean(item.get("description"))
    if description:
        line += f" : {description}"
    technologies = _join(item.get("technologies"))
    if technologies:
        line += f" [Technologies : {technologies}]"
    return line


def _education_line(item: dict[str, Any]) -> str:
    degree = ", ".join(
        part
        for part in (
            _clean(item.get("degree")),
            _clean(item.get("field_of_study")),
            _clean(item.get("school")),
        )
        if part
    )
    period = _period(item.get("start_year"), item.get("end_year"))
    return f"- {degree}" + (f" ({period})" if period else "")


def profile_to_text(profile: CandidateProfile) -> str:
    """Texte stable et lisible décrivant le profil : c'est lui qui sera vectorisé.

    Les préférences (contrat, lieu...) n'en font pas partie : elles servent de filtres.
    """
    lines: list[str] = []
    if _clean(profile.summary):
        lines.append(f"Résumé : {_clean(profile.summary)}")
    if _clean(profile.objectives):
        lines.append(f"Objectifs : {_clean(profile.objectives)}")
    for label, values in (
        ("Compétences", profile.skills),
        ("Technologies", profile.technologies),
        ("Centres d'intérêt", profile.interests),
    ):
        joined = _join(values)
        if joined:
            lines.append(f"{label} : {joined}")

    experiences = [i for i in profile.experiences or [] if isinstance(i, dict)]
    if experiences:
        lines.append("Expériences :")
        lines.extend(_experience_line(item) for item in experiences)
    education = [i for i in profile.education or [] if isinstance(i, dict)]
    if education:
        lines.append("Formation :")
        lines.extend(_education_line(item) for item in education)

    text = "\n".join(lines)
    if len(text) > MAX_PROFILE_TEXT_CHARS:
        text = text[:MAX_PROFILE_TEXT_CHARS].rsplit("\n", 1)[0]  # coupe en fin de ligne
    return text


def profile_text_hash(text: str) -> str:
    """Empreinte du texte : si elle change, le vecteur du profil est périmé."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
