from fastapi.testclient import TestClient


def test_profile_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/profile")
    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_get_profile_returns_404_when_missing(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/api/v1/profile", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_patch_creates_first_manual_profile(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.patch(
        "/api/v1/profile", json={"skills": ["Python", "SQL"]}, headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 1
    assert body["source"] == "manual"
    assert body["skills"] == ["Python", "SQL"]


def test_patch_creates_new_version_and_keeps_other_fields(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    client.patch(
        "/api/v1/profile",
        json={"summary": "Ingénieure logiciel", "skills": ["Python"]},
        headers=auth_headers,
    )
    response = client.patch(
        "/api/v1/profile", json={"skills": ["Python", "Docker"]}, headers=auth_headers
    )
    body = response.json()
    assert body["version"] == 2
    assert body["skills"] == ["Python", "Docker"]
    assert body["summary"] == "Ingénieure logiciel"  # champ non envoyé : conservé


def test_patch_removes_duplicate_skills(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.patch(
        "/api/v1/profile",
        json={"skills": ["Python", "python", " Docker "]},
        headers=auth_headers,
    )
    assert response.json()["skills"] == ["Python", "Docker"]


def test_patch_rejects_unknown_field(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.patch(
        "/api/v1/profile", json={"password_hash": "x"}, headers=auth_headers
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["errors"][0]["field"] == "password_hash"


def test_preferences_defaults_then_put_then_get(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    default = client.get("/api/v1/preferences", headers=auth_headers).json()
    assert default["contract_types"] == []
    assert default["id"] is None

    payload = {"contract_types": ["internship"], "locations": ["Paris"], "remote_ok": True}
    put = client.put("/api/v1/preferences", json=payload, headers=auth_headers)
    assert put.status_code == 200

    read = client.get("/api/v1/preferences", headers=auth_headers).json()
    assert read["contract_types"] == ["internship"]
    assert read["remote_ok"] is True


def test_preferences_reject_invalid_contract_type(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.put(
        "/api/v1/preferences", json={"contract_types": ["freelance"]}, headers=auth_headers
    )
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_unknown_route_uses_same_error_format(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"