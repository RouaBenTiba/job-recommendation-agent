import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.cv_profile import get_llm_client
from app.core.config import get_settings
from app.main import app
from app.models.candidate_profile import CandidateProfile
from app.models.cv import CV
from app.schemas.profile import ProfileUpdate
from app.services.llm.base import LLMUnavailableError
from app.services.profiles import update_profile
from tests.llm_fakes import FakeLLM, profile_json

CV_TEXT = "Amel Trabelsi\nÉtudiante ingénieure. Python, FastAPI, Docker. Stage chez Société Exemple en 2025."


def use_llm(fake: FakeLLM) -> None:
    app.dependency_overrides[get_llm_client] = lambda: fake


def user_id(client: TestClient, headers: dict[str, str]) -> uuid.UUID:
    return uuid.UUID(client.get("/api/v1/auth/me", headers=headers).json()["id"])


def make_cv(db: Session, owner: uuid.UUID, text: str | None = CV_TEXT, status: str = "parsed") -> CV:
    cv = CV(
        user_id=owner,
        filename="cv.pdf",
        file_size_bytes=100,
        storage_path=f"{owner}/{uuid.uuid4()}.pdf",
        extracted_text=text,
        status=status,
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)
    return cv


def profiles_of(db: Session, owner: uuid.UUID) -> list[CandidateProfile]:
    return list(
        db.scalars(select(CandidateProfile).where(CandidateProfile.user_id == owner).order_by(CandidateProfile.version))
    )


def test_profile_is_built_and_stored_as_first_llm_version(
    client: TestClient, auth_headers: dict[str, str], db_session: Session
) -> None:
    owner = user_id(client, auth_headers)
    cv = make_cv(db_session, owner)
    llm = FakeLLM(profile_json())
    use_llm(llm)

    response = client.post(f"/api/v1/cvs/{cv.id}/profile", headers=auth_headers)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["version"] == 1 and body["is_current"] is True
    assert body["source"] == "llm" and body["cv_id"] == str(cv.id)
    assert body["extraction_model"] == "fake-model (profile_extraction_v1)"
    assert body["technologies"] == ["Python", "FastAPI", "Docker"]
    assert body["experiences"][0]["company"] == "Société Exemple"
    assert body["education"][0]["school"] == "ENIT"
    assert len(profiles_of(db_session, owner)) == 1
    # the CV text reached the LLM inside the delimiters
    assert "<cv>" in llm.calls[0][1] and "Python, FastAPI, Docker" in llm.calls[0][1]


def test_new_extraction_creates_a_new_version_and_keeps_history(
    client: TestClient, auth_headers: dict[str, str], db_session: Session
) -> None:
    owner = user_id(client, auth_headers)
    cv = make_cv(db_session, owner)
    use_llm(FakeLLM(profile_json(), profile_json(skills=["Communication"])))

    assert client.post(f"/api/v1/cvs/{cv.id}/profile", headers=auth_headers).status_code == 201
    second = client.post(f"/api/v1/cvs/{cv.id}/profile", headers=auth_headers)

    assert second.status_code == 201
    versions = profiles_of(db_session, owner)
    assert [(p.version, p.is_current) for p in versions] == [(1, False), (2, True)]
    assert second.json()["skills"] == ["Communication"]


def test_manual_profile_is_kept_in_history_after_an_extraction(
    client: TestClient, auth_headers: dict[str, str], db_session: Session
) -> None:
    owner = user_id(client, auth_headers)
    update_profile(db_session, owner, ProfileUpdate(summary="Écrit à la main"))
    cv = make_cv(db_session, owner)
    use_llm(FakeLLM(profile_json()))

    assert client.post(f"/api/v1/cvs/{cv.id}/profile", headers=auth_headers).status_code == 201

    manual, extracted = profiles_of(db_session, owner)
    assert (manual.source, manual.is_current, manual.summary) == ("manual", False, "Écrit à la main")
    assert (extracted.source, extracted.is_current, extracted.version) == ("llm", True, 2)


def test_invalid_answer_is_retried_then_succeeds(
    client: TestClient, auth_headers: dict[str, str], db_session: Session
) -> None:
    cv = make_cv(db_session, user_id(client, auth_headers))
    llm = FakeLLM("not json", profile_json())
    use_llm(llm)
    assert client.post(f"/api/v1/cvs/{cv.id}/profile", headers=auth_headers).status_code == 201
    assert len(llm.calls) == 2


def test_never_usable_answers_give_502_and_store_nothing(
    client: TestClient, auth_headers: dict[str, str], db_session: Session
) -> None:
    owner = user_id(client, auth_headers)
    cv = make_cv(db_session, owner)
    llm = FakeLLM("bad", "bad", "bad")
    use_llm(llm)

    response = client.post(f"/api/v1/cvs/{cv.id}/profile", headers=auth_headers)

    assert response.status_code == 502
    assert response.json()["code"] == "bad_gateway"
    assert len(llm.calls) == get_settings().llm_max_attempts
    assert profiles_of(db_session, owner) == []


def test_unavailable_llm_gives_503(
    client: TestClient, auth_headers: dict[str, str], db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.services.profile_extraction.time.sleep", lambda _: None)
    cv = make_cv(db_session, user_id(client, auth_headers))
    use_llm(FakeLLM(*(LLMUnavailableError("429", retryable=True) for _ in range(3))))

    response = client.post(f"/api/v1/cvs/{cv.id}/profile", headers=auth_headers)

    assert response.status_code == 503
    assert response.json()["code"] == "service_unavailable"


def test_missing_api_key_gives_503_without_calling_anything(
    client: TestClient, auth_headers: dict[str, str], db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    cv = make_cv(db_session, user_id(client, auth_headers))
    monkeypatch.setenv("GEMINI_API_KEY", "")
    get_settings.cache_clear()

    response = client.post(f"/api/v1/cvs/{cv.id}/profile", headers=auth_headers)

    assert response.status_code == 503
    assert "pas configurée" in response.json()["detail"]


@pytest.mark.parametrize(
    ("text", "status"), [(CV_TEXT, "uploaded"), (CV_TEXT, "failed"), (None, "parsed"), ("", "parsed")]
)
def test_cv_without_extracted_text_is_a_conflict(
    client: TestClient, auth_headers: dict[str, str], db_session: Session, text: str | None, status: str
) -> None:
    cv = make_cv(db_session, user_id(client, auth_headers), text=text, status=status)
    llm = FakeLLM()
    use_llm(llm)

    response = client.post(f"/api/v1/cvs/{cv.id}/profile", headers=auth_headers)

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"
    assert llm.calls == []  # no LLM call, no cost


def test_cv_of_someone_else_looks_like_it_does_not_exist(
    client: TestClient, auth_headers: dict[str, str], db_session: Session
) -> None:
    owner = user_id(client, auth_headers)
    cv = make_cv(db_session, owner)
    email = f"other-{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Motdepasse123!"})
    login = client.post("/api/v1/auth/login", data={"username": email, "password": "Motdepasse123!"})
    intruder = {"Authorization": f"Bearer {login.json()['access_token']}"}
    llm = FakeLLM()
    use_llm(llm)

    response = client.post(f"/api/v1/cvs/{cv.id}/profile", headers=intruder)

    assert response.status_code == 404
    assert llm.calls == []


def test_unknown_cv_is_404_and_invalid_id_is_422(client: TestClient, auth_headers: dict[str, str]) -> None:
    use_llm(FakeLLM())
    assert client.post(f"/api/v1/cvs/{uuid.uuid4()}/profile", headers=auth_headers).status_code == 404
    assert client.post("/api/v1/cvs/not-a-uuid/profile", headers=auth_headers).status_code == 422


def test_authentication_is_required(client: TestClient) -> None:
    use_llm(FakeLLM())
    response = client.post(f"/api/v1/cvs/{uuid.uuid4()}/profile")
    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"
