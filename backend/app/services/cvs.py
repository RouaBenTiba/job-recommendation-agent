import re
import uuid
from pathlib import PurePath

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.cv import CV
from app.models.user import User
from app.services import storage

PDF_MAGIC = b"%PDF-"


class CVUploadError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def sanitize_filename(filename: str | None) -> str:
    """Keep only the base name, without directories or control characters."""
    name = PurePath((filename or "").replace("\\", "/")).name
    name = re.sub(r"[\x00-\x1f\x7f]", "", name).strip()
    return name[:255]


def validate_pdf(filename: str, data: bytes) -> None:
    max_bytes = get_settings().max_cv_size_mb * 1024 * 1024
    if len(data) == 0:
        raise CVUploadError(400, "Le fichier est vide.")
    if len(data) > max_bytes:
        raise CVUploadError(413, f"Le fichier dépasse la taille maximale de {get_settings().max_cv_size_mb} Mo.")
    if not filename.lower().endswith(".pdf"):
        raise CVUploadError(415, "Seuls les fichiers PDF sont acceptés.")
    # The content decides, not the extension or the type announced by the browser.
    if not data.startswith(PDF_MAGIC):
        raise CVUploadError(415, "Le contenu du fichier n'est pas un PDF valide.")


def create_cv(db: Session, user: User, filename: str | None, data: bytes) -> CV:
    name = sanitize_filename(filename)
    validate_pdf(name, data)

    count = db.scalar(select(func.count()).select_from(CV).where(CV.user_id == user.id)) or 0
    if count >= get_settings().max_cvs_per_user:
        raise CVUploadError(409, "Nombre maximal de CV atteint : supprimez-en un avant d'en importer un autre.")

    cv_id = uuid.uuid4()
    relative_path = storage.build_relative_path(user.id, cv_id)
    storage.save_file(relative_path, data)
    try:
        cv = CV(
            id=cv_id,
            user_id=user.id,
            filename=name,
            content_type="application/pdf",
            file_size_bytes=len(data),
            storage_path=relative_path,
            status="uploaded",
        )
        db.add(cv)
        db.commit()
        db.refresh(cv)
    except Exception:
        # No orphan file if the database write fails.
        db.rollback()
        storage.delete_file(relative_path)
        raise
    return cv


def get_cv(db: Session, user_id: uuid.UUID, cv_id: uuid.UUID) -> CV | None:
    """Only returns a CV that belongs to the user."""
    return db.scalar(select(CV).where(CV.id == cv_id, CV.user_id == user_id))


def list_cvs(db: Session, user_id: uuid.UUID) -> list[CV]:
    return list(db.scalars(select(CV).where(CV.user_id == user_id).order_by(CV.created_at.desc())))
