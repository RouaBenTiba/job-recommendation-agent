import uuid
from collections.abc import Callable
from pathlib import Path

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings


@pytest.fixture
def isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    get_settings.cache_clear()
    return tmp_path


def upload(client: TestClient, headers: dict[str, str], pdf: bytes) -> str:
    response = client.post(
        "/api/v1/cvs",
        files={"file": ("cv.pdf", pdf, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def test_extract_text_of_an_uploaded_cv(
    client: TestClient,
    auth_headers: dict[str, str],
    isolated_storage: Path,
    make_pdf: Callable[[list[str]], bytes],
) -> None:
    pdf = make_pdf(["Roua Ben Tiba\nIngenieure logiciel\nPython SQL Docker AWS"])
    cv_id = upload(client, auth_headers, pdf)

    response = client.post(f"/api/v1/cvs/{cv_id}/extract", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "parsed"
    assert body["method"] == "text"
    assert "Python SQL Docker AWS" in body["text"]
    cv = client.get(f"/api/v1/cvs/{cv_id}", headers=auth_headers).json()
    assert cv["status"] == "parsed"


def test_blank_pdf_is_refused_and_marked_failed(
    client: TestClient, auth_headers: dict[str, str], isolated_storage: Path
) -> None:
    doc = pymupdf.open()
    doc.new_page()
    blank = doc.tobytes()
    doc.close()
    cv_id = upload(client, auth_headers, blank)

    response = client.post(f"/api/v1/cvs/{cv_id}/extract", headers=auth_headers)

    assert response.status_code == 422
    assert "Aucun texte exploitable" in response.json()["detail"]
    cv = client.get(f"/api/v1/cvs/{cv_id}", headers=auth_headers).json()
    assert cv["status"] == "failed"


def test_extract_requires_authentication(client: TestClient) -> None:
    response = client.post(f"/api/v1/cvs/{uuid.uuid4()}/extract")
    assert response.status_code == 401


def test_extract_unknown_cv_is_404(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(f"/api/v1/cvs/{uuid.uuid4()}/extract", headers=auth_headers)
    assert response.status_code == 404
