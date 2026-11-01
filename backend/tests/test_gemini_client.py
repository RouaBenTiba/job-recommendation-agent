from typing import Any

import httpx
import pytest
from google.genai import errors

from app.core.config import get_settings
from app.schemas.profile_extraction import ProfileExtraction
from app.services.llm.base import LLMNotConfiguredError, LLMUnavailableError
from app.services.llm.gemini import GeminiClient, build_gemini_client


class FakeResponse:
    def __init__(self, text: str | None) -> None:
        self.text = text


class FakeModels:
    def __init__(self, result: FakeResponse | Exception) -> None:
        self.result = result
        self.calls: list[dict[str, Any]] = []

    def generate_content(self, *, model: str, contents: str, config: Any) -> FakeResponse:
        self.calls.append({"model": model, "contents": contents, "config": config})
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class FakeSdk:
    def __init__(self, result: FakeResponse | Exception) -> None:
        self.models = FakeModels(result)


def make_client(result: FakeResponse | Exception) -> tuple[GeminiClient, FakeSdk]:
    sdk = FakeSdk(result)
    return GeminiClient(api_key="fake", model="some-model", timeout_seconds=5, client=sdk), sdk  # type: ignore[arg-type]


def test_request_uses_structured_json_output() -> None:
    client, sdk = make_client(FakeResponse('{"ok": true}'))
    result = client.generate_json("system rules", "the cv", ProfileExtraction)
    assert result == '{"ok": true}'
    call = sdk.models.calls[0]
    assert call["model"] == "some-model" and call["contents"] == "the cv"
    assert call["config"].system_instruction == "system rules"
    assert call["config"].response_mime_type == "application/json"
    assert call["config"].response_schema is ProfileExtraction


def test_empty_response_becomes_empty_text() -> None:
    client, _ = make_client(FakeResponse(None))
    assert client.generate_json("s", "u", ProfileExtraction) == ""


@pytest.mark.parametrize(
    ("error", "retryable"),
    [
        (errors.ClientError(429, {"error": {"message": "quota"}}), True),
        (errors.ServerError(503, {"error": {"message": "overloaded"}}), True),
        (errors.ClientError(400, {"error": {"message": "bad request"}}), False),
        (errors.ClientError(403, {"error": {"message": "key revoked"}}), False),
        (httpx.ReadTimeout("timeout"), True),
    ],
)
def test_provider_errors_are_translated(error: Exception, retryable: bool) -> None:
    client, _ = make_client(error)
    with pytest.raises(LLMUnavailableError) as info:
        client.generate_json("s", "my private cv text", ProfileExtraction)
    assert info.value.retryable is retryable
    assert "my private cv text" not in str(info.value)


def test_missing_key_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "")
    get_settings.cache_clear()
    with pytest.raises(LLMNotConfiguredError):
        build_gemini_client()


def test_client_is_built_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_MODEL", "some-configured-model")
    get_settings.cache_clear()
    assert build_gemini_client().model == "some-configured-model"
