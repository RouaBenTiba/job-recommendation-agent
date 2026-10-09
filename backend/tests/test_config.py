import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_settings_load_from_environment() -> None:
    settings = get_settings()
    assert settings.app_env == "test"
    assert settings.database_url.startswith("postgresql://")
    assert settings.gemini_api_key is not None


def test_secrets_are_masked_in_repr() -> None:
    settings = get_settings()
    assert "fake-gemini-key" not in repr(settings)
    assert settings.gemini_api_key is not None
    assert settings.gemini_api_key.get_secret_value() == "fake-gemini-key"


def test_database_url_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_production_rejects_default_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SECRET_KEY")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]
