from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user  # ADAPTER
from app.db.session import get_db
from app.models.user import User
from app.schemas.preference import PreferencesRead, PreferencesUpdate
from app.services.preferences import get_preferences, upsert_preferences

router = APIRouter(prefix="/preferences", tags=["preferences"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=PreferencesRead)
def read_preferences(current_user: CurrentUser, db: DbSession) -> PreferencesRead:
    preferences = get_preferences(db, current_user.id)
    if preferences is None:
        return PreferencesRead()  # valeurs par défaut, rien n'est enregistré
    return PreferencesRead.model_validate(preferences)


@router.put("", response_model=PreferencesRead)
def put_preferences(data: PreferencesUpdate, current_user: CurrentUser, db: DbSession) -> PreferencesRead:
    preferences = upsert_preferences(db, current_user.id, data)
    return PreferencesRead.model_validate(preferences)
