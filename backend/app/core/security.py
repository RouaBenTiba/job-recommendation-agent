"""Password hashing (Argon2id) and JWT access tokens."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings

_hasher = PasswordHasher()
# Used to spend the same time on unknown emails as on wrong passwords.
_DUMMY_HASH = _hasher.hash("dummy-password-for-constant-time")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return _hasher.verify(hashed_password, password)
    except (VerificationError, InvalidHashError):
        return False


def burn_password_check(password: str) -> None:
    """Dummy verification to avoid revealing whether an email exists."""
    verify_password(password, _DUMMY_HASH)


@dataclass(frozen=True)
class TokenPayload:
    sub: str
    jti: str
    exp: datetime


def create_access_token(subject: str) -> tuple[str, int]:
    """Return (token, lifetime in seconds)."""
    settings = get_settings()
    lifetime = timedelta(minutes=settings.access_token_expire_minutes)
    now = datetime.now(UTC)
    claims = {
        "sub": subject,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + lifetime,
    }
    token = jwt.encode(
        claims,
        settings.secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    return token, int(lifetime.total_seconds())


def decode_access_token(token: str) -> TokenPayload:
    """Raise jwt.PyJWTError if the token is invalid, tampered with or expired."""
    settings = get_settings()
    data = jwt.decode(
        token,
        settings.secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "sub", "jti"]},
    )
    return TokenPayload(
        sub=str(data["sub"]),
        jti=str(data["jti"]),
        exp=datetime.fromtimestamp(data["exp"], UTC),
    )
