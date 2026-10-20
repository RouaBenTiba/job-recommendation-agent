"""Extraction du texte d'un CV importé (US-4.2) : lecture, nettoyage, base."""

import logging
from dataclasses import replace
from typing import NoReturn

from sqlalchemy.orm import Session

from app.models.cv import CV
from app.services import storage
from app.services.pdf_text import ExtractedText, PDFTextError, extract_text
from app.services.text_cleaning import clean_text

logger = logging.getLogger(__name__)

# Sous ce nombre de caractères, le texte est inexploitable (scan, page blanche).
MIN_USABLE_CHARS = 30


class CVExtractionError(Exception):
    """L'extraction a échoué. Le message peut être montré à la candidate."""


def _fail(db: Session, cv: CV, message: str) -> NoReturn:
    cv.status = "failed"
    cv.error_message = message
    cv.extracted_text = None
    db.commit()
    raise CVExtractionError(message)


def extract_cv_text(db: Session, cv: CV) -> ExtractedText:
    """Lit le PDF du CV, en extrait le texte propre et met la base à jour.

    Succès : `status = "parsed"` et le texte est dans `extracted_text`.
    Échec : `status = "failed"`, la cause est dans `error_message`, et on lève
    `CVExtractionError`.
    """
    try:
        data = storage.resolve_path(cv.storage_path).read_bytes()
        extracted = extract_text(data)
    except FileNotFoundError:
        _fail(db, cv, "Le fichier du CV est introuvable.")
    except OSError:
        _fail(db, cv, "Le fichier du CV ne peut pas être lu.")
    except ValueError:
        _fail(db, cv, "Le chemin du fichier du CV est invalide.")
    except PDFTextError as exc:
        _fail(db, cv, str(exc))

    text = clean_text(extracted.text)
    if len(text) < MIN_USABLE_CHARS:
        _fail(
            db,
            cv,
            "Aucun texte exploitable dans ce PDF. " "S'il s'agit d'un scan, l'OCR doit être activé.",
        )

    cv.extracted_text = text
    cv.status = "parsed"
    cv.error_message = None
    db.commit()
    db.refresh(cv)
    return replace(extracted, text=text)
