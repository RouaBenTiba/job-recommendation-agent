"""Extraction du texte d'un PDF avec PyMuPDF (US-4.2, tâches 1, 2 et 3)."""

import logging
from dataclasses import dataclass

import pymupdf

from app.core.config import get_settings
from app.services.pdf_layout import Block, order_blocks
from app.services.pdf_ocr import ocr_available, ocr_pages

logger = logging.getLogger(__name__)


class PDFTextError(Exception):
    """Le PDF ne peut pas être lu. Le message peut être montré à la candidate."""


@dataclass(frozen=True)
class ExtractedText:
    text: str
    page_count: int
    pages_read: int
    truncated: bool
    method: str  # "text" (couche de texte du PDF) ou "ocr" (PDF scanné)


def page_text(page: pymupdf.Page) -> str:
    """Texte d'une page, dans l'ordre de lecture (colonnes comprises)."""
    blocks = [
        Block(x0, y0, x1, y1, text)
        for x0, y0, x1, y1, text, _number, block_type in page.get_text("blocks")
        if block_type == 0  # 0 = texte, 1 = image
    ]
    ordered = order_blocks(blocks, page.rect.width)
    return "\n".join(block.text.strip() for block in ordered)


def extract_text(data: bytes) -> ExtractedText:
    """Extrait le texte brut d'un PDF, avec des limites de pages et de caractères."""
    settings = get_settings()
    method = "text"
    try:
        with pymupdf.open(stream=data, filetype="pdf") as doc:
            if doc.needs_pass:
                raise PDFTextError("Le PDF est protégé par un mot de passe.")

            page_count = doc.page_count
            pages_to_read = min(page_count, settings.max_cv_pages)
            parts = [page_text(doc[index]) for index in range(pages_to_read)]
            text = "\n\n".join(parts)

            # Presque pas de texte : sans doute un scan, on tente l'OCR s'il est actif.
            if len(text.strip()) < settings.min_text_chars_before_ocr and ocr_available():
                try:
                    ocr_text = "\n\n".join(ocr_pages(doc, pages_to_read))
                except Exception as exc:  # Tesseract absent, langue manquante...
                    logger.warning("OCR impossible (%s)", type(exc).__name__)
                else:
                    if len(ocr_text.strip()) > len(text.strip()):
                        text, method = ocr_text, "ocr"
    except PDFTextError:
        raise
    except Exception as exc:  # la bibliothèque peut lever plusieurs types d'erreurs
        logger.warning("PDF illisible (%s)", type(exc).__name__)
        raise PDFTextError("Le fichier PDF est illisible ou corrompu.") from exc

    truncated = pages_to_read < page_count
    if len(text) > settings.max_extracted_chars:
        text = text[: settings.max_extracted_chars]
        truncated = True

    return ExtractedText(
        text=text,
        page_count=page_count,
        pages_read=pages_to_read,
        truncated=truncated,
        method=method,
    )
