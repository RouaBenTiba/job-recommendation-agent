"""US-4.3: build a structured candidate profile from the text of a CV with an LLM."""

import json
import logging
import re
import time
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile
from app.models.cv import CV
from app.schemas.common import dedupe
from app.schemas.profile import ProfileUpdate
from app.schemas.profile_extraction import ProfileExtraction
from app.services.llm.base import LLMClient, LLMUnavailableError
from app.services.profiles import get_current_profile

logger = logging.getLogger(__name__)

PROMPT_VERSION = "profile_extraction_v1"
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# Limits of the strict schema (app.schemas.profile).
SHORT, LONG, TAG, DATE = 100, 2000, 80, 20
MAX_EDUCATION, MAX_EXPERIENCES, MAX_TAGS, MAX_EXPERIENCE_TAGS = 20, 30, 100, 30
MAX_BACKOFF_SECONDS = 4


class ProfileExtractionError(Exception):
    """The LLM never returned a usable profile."""


class InvalidProfileOutputError(Exception):
    """One answer of the LLM is unusable. The message is safe to send back to the LLM."""


@lru_cache
def load_system_prompt() -> str:
    return (PROMPTS_DIR / f"{PROMPT_VERSION}.txt").read_text(encoding="utf-8").strip()


def build_user_prompt(cv_text: str, feedback: str | None = None) -> str:
    # The CV is data: it is delimited, and any attempt to close the delimiter is removed.
    safe_text = re.sub(r"</?cv\s*>", "", cv_text, flags=re.IGNORECASE)
    parts = ["Extract the profile from the CV below.", "<cv>", safe_text, "</cv>"]
    if feedback:
        parts.append(f"Your previous answer was rejected: {feedback} Return a corrected JSON object.")
    return "\n".join(parts)


# --- normalization: loose LLM output -> values accepted by the strict schema -------------


def _text(value: str | None, limit: int) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned[:limit] if cleaned else None


def _tags(values: list[str], limit: int) -> list[str]:
    cleaned = [tag for tag in (_text(value, TAG) for value in values) if tag]
    return dedupe(cleaned)[:limit]


def _year(value: int | None) -> int | None:
    return value if value is not None and 1950 <= value <= 2100 else None


def normalize_extraction(raw: ProfileExtraction) -> dict[str, Any]:
    education = []
    for item in raw.education:
        school = _text(item.school, SHORT)
        if not school:
            continue
        start, end = _year(item.start_year), _year(item.end_year)
        if start and end and end < start:
            end = None
        education.append(
            {
                "school": school,
                "degree": _text(item.degree, SHORT),
                "field_of_study": _text(item.field_of_study, SHORT),
                "start_year": start,
                "end_year": end,
            }
        )

    experiences = []
    for exp in raw.experiences:
        company, title = _text(exp.company, SHORT), _text(exp.title, SHORT)
        if not company or not title:
            continue
        experiences.append(
            {
                "company": company,
                "title": title,
                "start": _text(exp.start, DATE),
                "end": _text(exp.end, DATE),
                "description": _text(exp.description, LONG),
                "technologies": _tags(exp.technologies, MAX_EXPERIENCE_TAGS),
            }
        )

    return {
        "summary": _text(raw.summary, LONG),
        "objectives": _text(raw.objectives, LONG),
        "education": education[:MAX_EDUCATION],
        "experiences": experiences[:MAX_EXPERIENCES],
        "skills": _tags(raw.skills, MAX_TAGS),
        "technologies": _tags(raw.technologies, MAX_TAGS),
        "interests": _tags(raw.interests, MAX_TAGS),
    }


def _describe(exc: ValidationError) -> str:
    # Field paths and messages only: the received values (CV content) are never repeated.
    problems = [f"{'.'.join(str(part) for part in err['loc'])}: {err['msg']}" for err in exc.errors()[:10]]
    return "; ".join(problems)


def parse_profile(raw_json: str) -> ProfileUpdate:
    """Parse and validate one answer. Raises InvalidProfileOutputError if it is unusable."""
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        raise InvalidProfileOutputError("the answer was not valid JSON.") from None
    try:
        loose = ProfileExtraction.model_validate(data)
        profile = ProfileUpdate.model_validate(normalize_extraction(loose))
    except ValidationError as exc:
        raise InvalidProfileOutputError(f"the answer did not match the schema ({_describe(exc)}).") from None
    if not (profile.skills or profile.technologies or profile.experiences or profile.education):
        raise InvalidProfileOutputError("no skill, technology, experience or education was extracted.")
    return profile


# --- LLM call with retries ----------------------------------------------------------------


def extract_profile(
    llm: LLMClient,
    cv_text: str,
    *,
    max_attempts: int,
    sleep: Callable[[float], None] | None = None,
) -> ProfileUpdate:
    pause = sleep if sleep is not None else time.sleep  # looked up at call time (patchable)
    system_prompt = load_system_prompt()
    feedback: str | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            raw = llm.generate_json(system_prompt, build_user_prompt(cv_text, feedback), ProfileExtraction)
        except LLMUnavailableError as exc:
            if not exc.retryable or attempt == max_attempts:
                raise
            logger.warning("LLM unavailable (attempt %d/%d), retrying", attempt, max_attempts)
            pause(min(2 ** (attempt - 1), MAX_BACKOFF_SECONDS))
            continue
        try:
            return parse_profile(raw)
        except InvalidProfileOutputError as exc:
            feedback = str(exc)
            logger.warning("Unusable LLM answer (attempt %d/%d): %s", attempt, max_attempts, feedback)
    raise ProfileExtractionError(f"No usable profile after {max_attempts} attempts.")


# --- persistence --------------------------------------------------------------------------


def save_llm_profile(db: Session, cv: CV, profile: ProfileUpdate, llm: LLMClient) -> CandidateProfile:
    """Store the profile as a NEW version (source "llm"); previous versions are kept."""
    values = profile.model_dump(mode="json")
    for field in ("education", "experiences", "skills", "technologies", "interests"):
        values[field] = values[field] or []

    current = get_current_profile(db, cv.user_id)
    version = 1
    if current is not None:
        version = current.version + 1
        current.is_current = False
        db.flush()  # frees the "one current version per user" index before the insert

    new_profile = CandidateProfile(
        user_id=cv.user_id,
        cv_id=cv.id,
        version=version,
        is_current=True,
        source="llm",
        extraction_model=f"{llm.model} ({PROMPT_VERSION})"[:100],
        **values,
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile
