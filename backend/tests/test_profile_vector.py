from collections.abc import Iterator

import pytest

from app.models.candidate_profile import CandidateProfile
from app.services import profile_vector
from app.services.profile_vector import refresh_profile_vector, set_profile_vectorizer


class Recorder:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def refresh(self, profile: CandidateProfile, text: str) -> None:
        self.texts.append(text)


class Broken:
    def refresh(self, profile: CandidateProfile, text: str) -> None:
        raise RuntimeError("service d'embeddings indisponible")


@pytest.fixture(autouse=True)
def _restore_vectorizer() -> Iterator[None]:
    previous = profile_vector._vectorizer
    yield
    set_profile_vectorizer(previous)


def test_refresh_gives_the_profile_text_to_the_vectorizer() -> None:
    recorder = Recorder()
    set_profile_vectorizer(recorder)

    refresh_profile_vector(CandidateProfile(skills=["Python"]))

    assert recorder.texts == ["Compétences : Python"]


def test_empty_profile_is_not_vectorized() -> None:
    recorder = Recorder()
    set_profile_vectorizer(recorder)

    refresh_profile_vector(CandidateProfile())

    assert recorder.texts == []


def test_a_failing_vectorizer_never_raises() -> None:
    set_profile_vectorizer(Broken())

    refresh_profile_vector(CandidateProfile(skills=["Python"]))  # ne doit pas lever


def test_default_vectorizer_does_nothing() -> None:
    refresh_profile_vector(CandidateProfile(skills=["Python"]))
