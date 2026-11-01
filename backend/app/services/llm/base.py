"""Provider-independent interface for the LLM (the rest of the code never imports Gemini)."""

from typing import Protocol

from pydantic import BaseModel


class LLMError(Exception):
    """Base class for LLM errors."""


class LLMNotConfiguredError(LLMError):
    """No API key is configured."""


class LLMUnavailableError(LLMError):
    """The provider could not answer (network, quota, server error...)."""

    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.retryable = retryable


class LLMClient(Protocol):
    model: str

    def generate_json(self, system_prompt: str, user_prompt: str, schema: type[BaseModel]) -> str:
        """Return the raw JSON text produced by the model for the given schema."""
        ...
