import shutil
from collections.abc import Callable

import pymupdf
import pytest

from app.core.config import get_settings
from app.services.pdf_text import PDFTextError, extract_text

TextBox = tuple[tuple[float, float, float, float], str]


def test_extracts_text_of_a_simple_pdf(make_pdf: Callable[[list[str]], bytes]) -> None:
    result = extract_text(make_pdf(["Roua Ben Tiba\nIngenieure logiciel\nPython, SQL"]))

    assert "Roua Ben Tiba" in result.text
    assert "Python, SQL" in result.text
    assert result.page_count == 1
    assert result.pages_read == 1
    assert result.truncated is False
    assert result.method == "text"


def test_reads_all_pages_in_order(make_pdf: Callable[[list[str]], bytes]) -> None:
    result = extract_text(make_pdf(["PAGE-UN", "PAGE-DEUX"]))

    assert result.page_count == 2
    assert result.text.index("PAGE-UN") < result.text.index("PAGE-DEUX")


def test_page_limit_truncates(make_pdf: Callable[[list[str]], bytes], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_CV_PAGES", "2")
    get_settings.cache_clear()

    result = extract_text(make_pdf(["AAA", "BBB", "CCC", "DDD"]))

    assert result.page_count == 4
    assert result.pages_read == 2
    assert result.truncated is True
    assert "CCC" not in result.text


def test_character_limit_truncates(make_pdf: Callable[[list[str]], bytes], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_EXTRACTED_CHARS", "50")
    get_settings.cache_clear()

    result = extract_text(make_pdf(["mot " * 100]))

    assert len(result.text) == 50
    assert result.truncated is True


def test_corrupted_pdf_raises_a_clear_error() -> None:
    with pytest.raises(PDFTextError, match="illisible"):
        extract_text(b"%PDF-1.7 ceci n'est pas un vrai pdf")


def test_password_protected_pdf_is_rejected() -> None:
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "secret")
    protected = doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="mdp", owner_pw="mdp")
    doc.close()

    with pytest.raises(PDFTextError, match="mot de passe"):
        extract_text(protected)


def test_blank_pdf_returns_empty_text() -> None:
    doc = pymupdf.open()
    doc.new_page()
    data = doc.tobytes()
    doc.close()

    assert extract_text(data).text.strip() == ""


# ---- Mises en page (tâche 2) --------------------------------------------------------


def test_sidebar_layout_is_read_column_by_column(
    make_layout_pdf: Callable[[list[TextBox]], bytes],
) -> None:
    pdf = make_layout_pdf(
        [
            ((30, 30, 565, 60), "ROUA BEN TIBA"),
            ((30, 100, 170, 180), "CONTACT\nroua@example.com"),
            ((30, 260, 170, 360), "COMPETENCES\nPython\nSQL"),
            ((200, 105, 560, 200), "EXPERIENCE\nStage chez Acme"),
            ((200, 300, 560, 400), "FORMATION\nCycle ingenieur"),
        ]
    )
    text = extract_text(pdf).text

    positions = [text.index(word) for word in ("CONTACT", "COMPETENCES", "EXPERIENCE", "FORMATION")]
    assert positions == sorted(positions)
    assert text.index("ROUA BEN TIBA") < text.index("CONTACT")


def test_timeline_layout_keeps_dates_next_to_their_description(
    make_layout_pdf: Callable[[list[TextBox]], bytes],
) -> None:
    pdf = make_layout_pdf(
        [
            ((40, 100, 130, 120), "2022-2024"),
            ((150, 100, 550, 160), "Acme Developpeur"),
            ((40, 220, 130, 240), "2020-2022"),
            ((150, 220, 550, 280), "Beta Stagiaire"),
            ((40, 340, 130, 360), "2018-2020"),
            ((150, 340, 550, 400), "Gamma Technicien"),
        ]
    )
    text = extract_text(pdf).text

    assert text.index("2022-2024") < text.index("Acme") < text.index("2020-2022")
    assert text.index("2020-2022") < text.index("Beta") < text.index("2018-2020")


# ---- OCR (tâche 3, extension) ----------------------------------------------


def make_scanned_pdf() -> bytes:
    """Un PDF qui ne contient qu'une image de texte, comme un document scanné."""
    source = pymupdf.open()
    page = source.new_page()
    page.insert_textbox(
        pymupdf.Rect(50, 50, 500, 300),
        "Roua Ben Tiba\nIngenieure logiciel\nPython SQL Docker AWS Kubernetes",
        fontsize=18,
    )
    png = page.get_pixmap(dpi=200).tobytes("png")
    source.close()

    scan = pymupdf.open()
    scan_page = scan.new_page(width=595, height=842)
    scan_page.insert_image(scan_page.rect, stream=png)
    data: bytes = scan.tobytes()
    scan.close()
    return data


def test_scanned_pdf_gives_no_text_when_ocr_is_disabled() -> None:
    result = extract_text(make_scanned_pdf())

    assert result.text.strip() == ""
    assert result.method == "text"


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract n'est pas installé")
def test_scanned_pdf_is_read_with_ocr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OCR_ENABLED", "true")
    get_settings.cache_clear()

    result = extract_text(make_scanned_pdf())

    assert result.method == "ocr"
    assert "Python" in result.text
    assert "Docker" in result.text
