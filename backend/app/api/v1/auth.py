from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession, ValidToken
from app.core.security import (
    burn_password_check,
    create_access_token,
    verify_password,
)
from app.schemas.auth import Token, UserCreate, UserRead
from app.services import tokens, users

router = APIRouter(prefix="/auth", tags=["auth"])


def _bad_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: DbSession) -> UserRead:
    if users.get_user_by_email(db, data.email) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    try:
        user = users.create_user(db, data.email, data.password, data.full_name)
    except IntegrityError:  # concurrent registration with the same email
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered") from None
    return UserRead.model_validate(user)


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession) -> Token:
    """OAuth2 password flow: send `username` (the email) and `password` as a form."""
    user = users.get_user_by_email(db, form.username)
    if user is None:
        burn_password_check(form.password)
        raise _bad_credentials()
    if not verify_password(form.password, user.password_hash) or not user.is_active:
        raise _bad_credentials()
    users.mark_logged_in(db, user)
    token, expires_in = create_access_token(str(user.id))
    return Token(access_token=token, expires_in=expires_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: ValidToken, db: DbSession) -> Response:
    tokens.revoke(db, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
