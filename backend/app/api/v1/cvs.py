import uuid
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.models.cv import CV
from app.schemas.cv import CVRead
from app.services import cvs
from app.services.cvs import CVUploadError

router = APIRouter(prefix="/cvs", tags=["cvs"])


@router.post("", response_model=CVRead, status_code=status.HTTP_201_CREATED)
def upload_cv(
    file: Annotated[UploadFile, File(description="CV au format PDF")],
    current_user: CurrentUser,
    db: DbSession,
) -> CV:
    # Read at most one byte more than the limit: enough to detect an oversized file.
    max_bytes = get_settings().max_cv_size_mb * 1024 * 1024
    data = file.file.read(max_bytes + 1)
    try:
        return cvs.create_cv(db, current_user, file.filename, data)
    except CVUploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from None


@router.get("", response_model=list[CVRead])
def list_my_cvs(current_user: CurrentUser, db: DbSession) -> list[CV]:
    return cvs.list_cvs(db, current_user.id)


@router.get("/{cv_id}", response_model=CVRead)
def read_cv(cv_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> CV:
    cv = cvs.get_cv(db, current_user.id, cv_id)
    if cv is None:  # same answer for "does not exist" and "belongs to someone else"
        raise HTTPException(status_code=404, detail="CV introuvable.")
    return cv
