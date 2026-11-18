from app.models.candidate_profile import CandidateProfile
from app.services.profile_text import (
    MAX_PROFILE_TEXT_CHARS,
    profile_text_hash,
    profile_to_text,
)


def make_profile() -> CandidateProfile:
    return CandidateProfile(
        summary="Ingénieure data junior",
        objectives="Stage de fin d'études",
        skills=["Python", "SQL"],
        technologies=["Docker", "Airflow"],
        interests=["Cloud"],
        experiences=[
            {
                "title": "Stagiaire Data Engineer",
                "company": "Acme",
                "start": "2025-06",
                "end": "2025-08",
                "description": "Pipeline ETL",
                "technologies": ["Airflow", "PostgreSQL"],
            }
        ],
        education=[
            {
                "school": "Université de Lyon",
                "degree": "Master",
                "field_of_study": "Informatique",
                "start_year": 2024,
                "end_year": 2026,
            }
        ],
    )


def test_text_contains_every_section() -> None:
    text = profile_to_text(make_profile())

    assert "Résumé : Ingénieure data junior" in text
    assert "Compétences : Python, SQL" in text
    assert "Technologies : Docker, Airflow" in text
    assert "- Stagiaire Data Engineer chez Acme (2025-06 - 2025-08) : Pipeline ETL" in text
    assert "[Technologies : Airflow, PostgreSQL]" in text
    assert "- Master, Informatique, Université de Lyon (2024 - 2026)" in text


def test_text_is_stable() -> None:
    assert profile_to_text(make_profile()) == profile_to_text(make_profile())


def test_empty_profile_gives_empty_text() -> None:
    assert profile_to_text(CandidateProfile()) == ""


def test_unusable_items_are_ignored() -> None:
    profile = CandidateProfile(skills=["Python", "", None], experiences=["pas un dict"])

    assert profile_to_text(profile) == "Compétences : Python"


def test_text_is_truncated_on_a_line_boundary() -> None:
    profile = CandidateProfile(summary="mot " * 3000, skills=["Python"])

    text = profile_to_text(profile)

    assert len(text) <= MAX_PROFILE_TEXT_CHARS


def test_hash_changes_with_the_content() -> None:
    first = profile_text_hash(profile_to_text(make_profile()))
    changed = make_profile()
    changed.skills = ["Python", "Rust"]

    assert first != profile_text_hash(profile_to_text(changed))
    assert first == profile_text_hash(profile_to_text(make_profile()))
