"""Configuration de l'application, chargée depuis l'environnement et backend/.env."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "change-me-in-production"  # noqa: S105 (valeur de dev, refusée en prod)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    secret_key: SecretStr = SecretStr(DEFAULT_SECRET_KEY)
    cors_origins: list[str] = ["http://localhost:5173"]

    database_url: str

    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-2.5-flash"

    adzuna_app_id: str | None = None
    adzuna_app_key: SecretStr | None = None
    jooble_api_key: SecretStr | None = None
    tavily_api_key: SecretStr | None = None

    langfuse_public_key: str | None = None
    langfuse_secret_key: SecretStr | None = None

    @model_validator(mode="after")
    def _check_production(self) -> "Settings":
        if self.app_env == "production":
            if self.secret_key.get_secret_value() == DEFAULT_SECRET_KEY:
                raise ValueError("SECRET_KEY doit être défini en production")
            if self.gemini_api_key is None:
                raise ValueError("GEMINI_API_KEY est requis en production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
