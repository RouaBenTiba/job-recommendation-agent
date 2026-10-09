import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import TokenPayload, decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services import tokens, users

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DbSession = Annotated[Session, Depends(get_db)]


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_token_payload(token: Annotated[str, Depends(oauth2_scheme)], db: DbSession) -> TokenPayload:
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise _unauthorized() from None
    if tokens.is_revoked(db, payload.jti):
        raise _unauthorized()
    return payload


ValidToken = Annotated[TokenPayload, Depends(get_token_payload)]


def get_current_user(payload: ValidToken, db: DbSession) -> User:
    try:
        user_id = uuid.UUID(payload.sub)
    except ValueError:
        raise _unauthorized() from None
    user = users.get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise _unauthorized()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
