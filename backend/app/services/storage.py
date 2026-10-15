"""Local disk storage for uploaded CVs (object storage such as S3 is planned for production)."""

import os
import uuid
from pathlib import Path

from app.core.config import get_settings


def storage_root() -> Path:
    root = get_settings().storage_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def build_relative_path(user_id: uuid.UUID, cv_id: uuid.UUID) -> str:
    """Path relative to the storage root. Built only from UUIDs, never from user input."""
    return f"{user_id}/{cv_id}.pdf"


def resolve_path(relative_path: str) -> Path:
    root = storage_root()
    path = (root / relative_path).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Invalid storage path")
    return path


def save_file(relative_path: str, data: bytes) -> None:
    path = resolve_path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "xb") as file:  # "x": never overwrite an existing file
        file.write(data)
    os.chmod(path, 0o600)  # owner only (no effect on Windows)


def delete_file(relative_path: str) -> None:
    resolve_path(relative_path).unlink(missing_ok=True)
