"""Gemini implementation of the LLMClient interface (google-genai SDK)."""

import logging

import httpx
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from app.core.config import get_settings
from app.services.llm.base import LLMNotConfiguredError, LLMUnavailableError

logger = logging.getLogger(__name__)

RETRYABLE_STATUS = {408, 429}


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: int,
        client: genai.Client | None = None,
    ) -> None:
        self.model = model
        # The SDK expresses the timeout in milliseconds.
        self._client = client or genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=timeout_seconds * 1000),
        )

    def generate_json(self, system_prompt: str, user_prompt: str, schema: type[BaseModel]) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=schema,
        )
        try:
            response = self._client.models.generate_content(model=self.model, contents=user_prompt, config=config)
        except errors.APIError as exc:
            retryable = exc.code in RETRYABLE_STATUS or exc.code >= 500
            # Only the status code is logged: never the prompt, which contains the CV.
            logger.warning("Gemini API error %s (model %s)", exc.code, self.model)
            raise LLMUnavailableError(f"Gemini API error {exc.code}", retryable=retryable) from None
        except httpx.HTTPError as exc:
            logger.warning("Gemini network error: %s", type(exc).__name__)
            raise LLMUnavailableError("Gemini network error", retryable=True) from None
        return response.text or ""


def build_gemini_client() -> GeminiClient:
    settings = get_settings()
    key = settings.gemini_api_key.get_secret_value().strip() if settings.gemini_api_key else ""
    if not key:
        raise LLMNotConfiguredError("GEMINI_API_KEY is not set")
    return GeminiClient(api_key=key, model=settings.gemini_model, timeout_seconds=settings.llm_timeout_seconds)
