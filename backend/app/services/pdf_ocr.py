"""OCR de secours pour les PDF scannés (US-4.2, tâche 3, extension).

Nécessite le programme Tesseract installé sur la machine, avec les langues voulues
(par exemple `tesseract-ocr` et `tesseract-ocr-fra` sous Debian). Désactivé par défaut.
"""

import logging
import shutil

import pymupdf

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def ocr_available() -> bool:
    """L'OCR est utilisable s'il est activé et que Tesseract est installé."""
    return get_settings().ocr_enabled and shutil.which("tesseract") is not None


def ocr_pages(doc: pymupdf.Document, page_count: int) -> list[str]:
    """Lit les `page_count` premières pages par reconnaissance de caractères."""
    settings = get_settings()
    texts: list[str] = []
    for index in range(page_count):
        page = doc[index]
        textpage = page.get_textpage_ocr(language=settings.ocr_languages, dpi=settings.ocr_dpi, full=True)
        texts.append(page.get_text("text", textpage=textpage, sort=True))
    return texts
