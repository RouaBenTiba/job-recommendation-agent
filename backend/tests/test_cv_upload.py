import re
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.cv import CV

PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
URL = "/api/v1/cvs"


@pytest.fixture(autouse=True)
def storage_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Every test writes into its own temporary directory."""
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    get_settings.cache_clear()
    return tmp_path


def upload(
    client: TestClient,
    headers: dict[str, str],
    content: bytes = PDF,
    filename: str = "cv.pdf",
    content_type: str = "application/pdf",
):  # type: ignore[no-untyped-def]
    return client.post(URL, headers=headers, files={"file": (filename, content, content_type)})


def stored_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file()]


def other_user_headers(client: TestClient) -> dict[str, str]:
    email = f"other-{uuid.uuid4().hex[:8]}@example.com"
    creds = {"email": email, "password": "Motdepasse123!"}
    assert client.post("/api/v1/auth/register", json=creds).status_code == 201
    login = client.post("/api/v1/auth/login", data={"username": email, "password": creds["password"]})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_upload_stores_file_and_metadata(
    client: TestClient, auth_headers: dict[str, str], db_session: Session, storage_dir: Path
) -> None:
    response = upload(client, auth_headers)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["filename"] == "cv.pdf"
    assert body["content_type"] == "application/pdf"
    assert body["file_size_bytes"] == len(PDF)
    assert body["status"] == "uploaded"
    assert "storage_path" not in body and "extracted_text" not in body

    cv = db_session.get(CV, uuid.UUID(body["id"]))
    assert cv is not None
    assert cv.file_size_bytes == len(PDF)
    assert (storage_dir / cv.storage_path).read_bytes() == PDF


def test_stored_name_is_random_and_never_the_original_name(
    client: TestClient, auth_headers: dict[str, str], db_session: Session, storage_dir: Path
) -> None:
    upload(client, auth_headers, filename="mon-cv-secret.pdf")
    (path,) = stored_files(storage_dir)
    assert "secret" not in str(path.relative_to(storage_dir))
    assert re.fullmatch(r"[0-9a-f-]{36}/[0-9a-f-]{36}\.pdf", path.relative_to(storage_dir).as_posix())


def test_path_traversal_in_filename_is_neutralised(
    client: TestClient, auth_headers: dict[str, str], storage_dir: Path
) -> None:
    response = upload(client, auth_headers, filename="../../../etc/passwd.pdf")
    assert response.status_code == 201
    assert response.json()["filename"] == "passwd.pdf"
    assert all(p.resolve().is_relative_to(storage_dir.resolve()) for p in stored_files(storage_dir))


def test_upload_requires_authentication(client: TestClient, storage_dir: Path) -> None:
    response = client.post(URL, files={"file": ("cv.pdf", PDF, "application/pdf")})
    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"
    assert stored_files(storage_dir) == []


def test_non_pdf_extension_is_rejected(client: TestClient, auth_headers: dict[str, str], storage_dir: Path) -> None:
    response = upload(client, auth_headers, filename="cv.txt")
    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_media_type"
    assert stored_files(storage_dir) == []


def test_fake_pdf_is_rejected_even_with_pdf_extension_and_type(
    client: TestClient, auth_headers: dict[str, str], storage_dir: Path
) -> None:
    response = upload(client, auth_headers, content=b"MZ\x90\x00 not a pdf at all", filename="cv.pdf")
    assert response.status_code == 415
    assert stored_files(storage_dir) == []


def test_empty_file_is_rejected(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert upload(client, auth_headers, content=b"").status_code == 400


def test_oversized_file_is_rejected_and_not_stored(
    client: TestClient,
    auth_headers: dict[str, str],
    db_session: Session,
    storage_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MAX_CV_SIZE_MB", "1")
    get_settings.cache_clear()
    response = upload(client, auth_headers, content=PDF + b"0" * (1024 * 1024))
    assert response.status_code == 413
    assert response.json()["code"] == "payload_too_large"
    assert stored_files(storage_dir) == []
    assert db_session.scalar(select(func.count()).select_from(CV)) == 0


def test_file_at_the_exact_limit_is_accepted(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAX_CV_SIZE_MB", "1")
    get_settings.cache_clear()
    content = PDF + b"0" * (1024 * 1024 - len(PDF))
    assert len(content) == 1024 * 1024
    assert upload(client, auth_headers, content=content).status_code == 201


def test_missing_file_field_is_a_validation_error(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(URL, headers=auth_headers)
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_cv_quota_per_user(
    client: TestClient, auth_headers: dict[str, str], storage_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAX_CVS_PER_USER", "2")
    get_settings.cache_clear()
    assert upload(client, auth_headers).status_code == 201
    assert upload(client, auth_headers).status_code == 201
    assert upload(client, auth_headers).status_code == 409
    assert len(stored_files(storage_dir)) == 2


def test_failed_database_write_leaves_no_orphan_file(
    client: TestClient,
    auth_headers: dict[str, str],
    db_session: Session,
    storage_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom() -> None:
        raise RuntimeError("database down")

    monkeypatch.setattr(db_session, "commit", boom)
    with pytest.raises(RuntimeError):
        upload(client, auth_headers)
    assert stored_files(storage_dir) == []


def test_read_own_cv_and_list(client: TestClient, auth_headers: dict[str, str]) -> None:
    cv_id = upload(client, auth_headers).json()["id"]
    assert client.get(f"{URL}/{cv_id}", headers=auth_headers).json()["id"] == cv_id
    listing = client.get(URL, headers=auth_headers).json()
    assert [item["id"] for item in listing] == [cv_id]


def test_a_cv_of_someone_else_looks_like_it_does_not_exist(client: TestClient, auth_headers: dict[str, str]) -> None:
    cv_id = upload(client, auth_headers).json()["id"]
    intruder = other_user_headers(client)
    response = client.get(f"{URL}/{cv_id}", headers=intruder)
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
    assert client.get(URL, headers=intruder).json() == []


def test_invalid_cv_id_is_a_validation_error(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.get(f"{URL}/not-a-uuid", headers=auth_headers).status_code == 422
