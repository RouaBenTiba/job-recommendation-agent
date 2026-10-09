import uuid

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token
from app.services import users

PASSWORD = "S3cret-pass!"
CREDS = {"email": "Roua@Example.com", "password": PASSWORD}


def register(client: TestClient) -> None:
    response = client.post("/api/v1/auth/register", json=CREDS)
    assert response.status_code == 201, response.text


def login(
    client: TestClient,
    email: str = "roua@example.com",
    password: str = PASSWORD,
) -> Response:
    return client.post("/api/v1/auth/login", data={"username": email, "password": password})


def auth_header(client: TestClient) -> dict[str, str]:
    register(client)
    token = login(client).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_returns_user_without_password(client: TestClient) -> None:
    response = client.post("/api/v1/auth/register", json=CREDS)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "roua@example.com"
    assert "password" not in body and "hashed_password" not in body


def test_register_duplicate_email_is_conflict(client: TestClient) -> None:
    register(client)
    response = client.post("/api/v1/auth/register", json={**CREDS, "email": "ROUA@example.com"})
    assert response.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "not-an-email", "password": PASSWORD},
        {"email": "a@example.com", "password": "short"},
        {"email": "a@example.com", "password": "x" * 129},
    ],
)
def test_register_validates_input(client: TestClient, payload: dict[str, str]) -> None:
    assert client.post("/api/v1/auth/register", json=payload).status_code == 422


def test_login_returns_bearer_token(client: TestClient) -> None:
    register(client)
    response = login(client)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == get_settings().access_token_expire_minutes * 60


def test_login_errors_do_not_reveal_which_part_is_wrong(client: TestClient) -> None:
    register(client)
    wrong_password = login(client, password="nope-nope-nope")
    unknown_email = login(client, email="ghost@example.com")
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_private_route_requires_token(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401
    bad = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"})
    assert bad.status_code == 401


def test_me_returns_current_user(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me", headers=auth_header(client))
    assert response.status_code == 200
    assert response.json()["email"] == "roua@example.com"


def test_logout_revokes_the_token(client: TestClient) -> None:
    headers = auth_header(client)
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 401


def test_expired_token_is_rejected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    register(client)
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "-1")
    get_settings.cache_clear()
    token, _ = create_access_token(str(uuid.uuid4()))
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_token_of_unknown_user_is_rejected(client: TestClient) -> None:
    token, _ = create_access_token(str(uuid.uuid4()))
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_register_accepts_optional_full_name(client: TestClient) -> None:
    response = client.post("/api/v1/auth/register", json={**CREDS, "full_name": "Roua Ben Tiba"})
    assert response.status_code == 201
    assert response.json()["full_name"] == "Roua Ben Tiba"
    assert uuid.UUID(response.json()["id"])


def test_login_updates_last_login(client: TestClient, db_session: Session) -> None:
    register(client)
    user = users.get_user_by_email(db_session, "roua@example.com")
    assert user is not None and user.last_login_at is None
    login(client)
    db_session.refresh(user)
    assert user.last_login_at is not None


def test_password_is_never_stored_in_clear(client: TestClient, db_session: Session) -> None:
    register(client)
    user = users.get_user_by_email(db_session, "roua@example.com")
    assert user is not None
    assert user.password_hash.startswith("$argon2")
    assert PASSWORD not in user.password_hash
