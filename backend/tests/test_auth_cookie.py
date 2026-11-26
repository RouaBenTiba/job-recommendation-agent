import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.deps import CSRF_HEADER, CSRF_VALUE
from app.core.config import Settings, get_settings

CSRF = {CSRF_HEADER: CSRF_VALUE}
EMAIL = "cookie@example.com"
PASSWORD = "Motdepasse123!"
COOKIE = "access_token"


def register(client: TestClient) -> None:
    assert client.post("/api/v1/auth/register", json={"email": EMAIL, "password": PASSWORD}).status_code == 201


def login(client: TestClient, headers: dict[str, str] | None = None):  # type: ignore[no-untyped-def]
    return client.post("/api/v1/auth/login", data={"username": EMAIL, "password": PASSWORD}, headers=headers or {})


def test_login_with_csrf_header_sets_an_httponly_session_cookie(client: TestClient) -> None:
    register(client)
    response = login(client, CSRF)
    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert cookie.startswith(f"{COOKIE}=")
    for attribute in (
        "httponly",
        "samesite=lax",
        "path=/",
        f"max-age={get_settings().access_token_expire_minutes * 60}",
    ):
        assert attribute in cookie
    assert "secure" not in cookie  # off in test/dev (plain http)


def test_login_without_the_header_never_sets_a_cookie(client: TestClient) -> None:
    register(client)
    response = login(client)  # what a cross-site form post or Swagger sends
    assert response.status_code == 200
    assert "set-cookie" not in response.headers
    assert response.json()["access_token"]  # Swagger and API clients still get the token


def test_cookie_is_secure_when_configured(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COOKIE_SECURE", "true")
    get_settings.cache_clear()
    register(client)
    assert "secure" in login(client, CSRF).headers["set-cookie"].lower()


def test_cookie_authenticates_reads(client: TestClient) -> None:
    register(client)
    login(client, CSRF)
    response = client.get("/api/v1/auth/me")  # no Authorization header, no CSRF header on a GET
    assert response.status_code == 200
    assert response.json()["email"] == EMAIL


def test_cookie_authenticated_writes_need_the_csrf_header(client: TestClient) -> None:
    register(client)
    login(client, CSRF)
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"
    assert client.get("/api/v1/auth/me").status_code == 200  # session untouched


def test_logout_revokes_the_token_and_clears_the_cookie(client: TestClient) -> None:
    register(client)
    token = login(client, CSRF).json()["access_token"]
    response = client.post("/api/v1/auth/logout", headers=CSRF)
    assert response.status_code == 204
    cleared = response.headers["set-cookie"].lower()
    assert f"{COOKIE}=" in cleared and ("max-age=0" in cleared or "expires=" in cleared)
    assert client.get("/api/v1/auth/me").status_code == 401  # cookie gone
    stolen = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert stolen.status_code == 401  # and the token itself is revoked


def test_bearer_header_does_not_need_the_csrf_header(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.post("/api/v1/auth/logout", headers=auth_headers).status_code == 204


def test_invalid_cookie_is_unauthorized(client: TestClient) -> None:
    client.cookies.set(COOKIE, "garbage")
    assert client.get("/api/v1/auth/me").status_code == 401


def test_missing_credentials_keep_the_same_answer(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json() == {"code": "unauthorized", "detail": "Not authenticated"}


def test_production_requires_a_secure_cookie(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "a-real-production-key-with-enough-length-1234")
    with pytest.raises(ValidationError, match="COOKIE_SECURE"):
        Settings(_env_file=None)  # type: ignore[call-arg]
    monkeypatch.setenv("COOKIE_SECURE", "true")
    Settings(_env_file=None)  # type: ignore[call-arg]
