from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.models.candidate_profile import CandidateProfile
from app.services import profile_vector
from app.services.profile_vector import set_profile_vectorizer


def make_two_versions(client: TestClient, headers: dict[str, str]) -> None:
    client.patch("/api/v1/profile", json={"skills": ["Python"]}, headers=headers)
    client.patch("/api/v1/profile", json={"skills": ["Python", "Docker"]}, headers=headers)


def test_versions_are_listed_newest_first(client: TestClient, auth_headers: dict[str, str]) -> None:
    make_two_versions(client, auth_headers)

    response = client.get("/api/v1/profile/versions", headers=auth_headers)

    assert response.status_code == 200
    versions = response.json()
    assert [v["version"] for v in versions] == [2, 1]
    assert [v["is_current"] for v in versions] == [True, False]


def test_read_an_old_version(client: TestClient, auth_headers: dict[str, str]) -> None:
    make_two_versions(client, auth_headers)

    response = client.get("/api/v1/profile/versions/1", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["skills"] == ["Python"]


def test_unknown_version_is_404(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/profile/versions/9", headers=auth_headers)

    assert response.status_code == 404


def test_version_number_must_be_positive(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/profile/versions/0", headers=auth_headers)

    assert response.status_code == 422


def test_restore_creates_a_new_current_version(client: TestClient, auth_headers: dict[str, str]) -> None:
    make_two_versions(client, auth_headers)

    response = client.post("/api/v1/profile/versions/1/restore", headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["version"] == 3
    assert body["skills"] == ["Python"]
    assert body["is_current"] is True
    versions = client.get("/api/v1/profile/versions", headers=auth_headers).json()
    assert [v["version"] for v in versions] == [3, 2, 1]
    assert [v["is_current"] for v in versions] == [True, False, False]


def test_restore_the_current_version_is_a_conflict(client: TestClient, auth_headers: dict[str, str]) -> None:
    make_two_versions(client, auth_headers)

    response = client.post("/api/v1/profile/versions/2/restore", headers=auth_headers)

    assert response.status_code == 409


def test_versions_require_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/profile/versions").status_code == 401


# ---- Task 4 : le vecteur est recalculé après chaque changement -------------------


class Recorder:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def refresh(self, profile: CandidateProfile, text: str) -> None:
        self.texts.append(text)


@pytest.fixture
def recorder() -> Iterator[Recorder]:
    previous = profile_vector._vectorizer
    recorder = Recorder()
    set_profile_vectorizer(recorder)
    yield recorder
    set_profile_vectorizer(previous)


def test_patch_refreshes_the_profile_vector(
    client: TestClient, auth_headers: dict[str, str], recorder: Recorder
) -> None:
    client.patch("/api/v1/profile", json={"skills": ["Python"]}, headers=auth_headers)

    assert recorder.texts == ["Compétences : Python"]


def test_restore_refreshes_the_profile_vector(
    client: TestClient, auth_headers: dict[str, str], recorder: Recorder
) -> None:
    make_two_versions(client, auth_headers)
    recorder.texts.clear()

    client.post("/api/v1/profile/versions/1/restore", headers=auth_headers)

    assert recorder.texts == ["Compétences : Python"]
