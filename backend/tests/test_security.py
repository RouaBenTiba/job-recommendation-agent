import jwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_is_hashed_with_argon2() -> None:
    hashed = hash_password("correct horse")
    assert hashed != "correct horse"
    assert hashed.startswith("$argon2")
    assert verify_password("correct horse", hashed)
    assert not verify_password("wrong", hashed)


def test_verify_password_rejects_garbage_hash() -> None:
    assert not verify_password("x", "not-a-hash")


def test_token_roundtrip() -> None:
    token, expires_in = create_access_token("42")
    payload = decode_access_token(token)
    assert payload.sub == "42"
    assert payload.jti
    assert expires_in == get_settings().access_token_expire_minutes * 60


def test_tampered_token_is_rejected() -> None:
    token, _ = create_access_token("42")
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token[:-2] + "xx")


def test_expired_token_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "-1")
    get_settings.cache_clear()
    token, _ = create_access_token("42")
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)
