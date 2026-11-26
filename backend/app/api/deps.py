import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import TokenPayload, decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services import tokens, users

# auto_error=False: the token may also come from the session cookie (browser frontend).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
# Custom header required on state-changing requests authenticated by the cookie. A browser
# cannot add it to a cross-site form or image request, and cross-origin scripts need a
# CORS preflight that only the configured origins pass.
CSRF_HEADER = "X-CSRF-Protection"
CSRF_VALUE = "1"


def has_csrf_header(request: Request) -> bool:
    return request.headers.get(CSRF_HEADER) == CSRF_VALUE


def _unauthorized(detail: str = "Invalid or expired token") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_token_payload(
    request: Request,
    bearer_token: Annotated[str | None, Depends(oauth2_scheme)],
    db: DbSession,
) -> TokenPayload:
    token = bearer_token  # an explicit Authorization header wins over the cookie
    if token is None:
        token = request.cookies.get(get_settings().cookie_name)
        if token is not None and request.method not in SAFE_METHODS and not has_csrf_header(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Requête refusée : en-tête de protection CSRF manquant.",
            )
    if token is None:
        raise _unauthorized("Not authenticated")
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
