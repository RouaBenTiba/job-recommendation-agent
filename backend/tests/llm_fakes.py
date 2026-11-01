import json
from typing import Any

from pydantic import BaseModel


class FakeLLM:
    """Replaces the real LLM in every test: no network call, no real key."""

    model = "fake-model"

    def __init__(self, *responses: str | Exception) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, str]] = []

    def generate_json(self, system_prompt: str, user_prompt: str, schema: type[BaseModel]) -> str:
        self.calls.append((system_prompt, user_prompt))
        if not self.responses:
            raise AssertionError("unexpected LLM call")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def profile_json(**overrides: Any) -> str:
    """A valid LLM answer; override fields to build variants."""
    data: dict[str, Any] = {
        "summary": "Étudiante ingénieure à la recherche d'un stage.",
        "objectives": None,
        "education": [
            {
                "school": "ENIT",
                "degree": "Cycle ingénieur",
                "field_of_study": "Informatique",
                "start_year": 2023,
                "end_year": 2026,
            }
        ],
        "experiences": [
            {
                "company": "Société Exemple",
                "title": "Stagiaire développeuse",
                "start": "2025-06",
                "end": "2025-08",
                "description": "Application de gestion de stocks.",
                "technologies": ["FastAPI", "React"],
            }
        ],
        "skills": ["Travail en équipe"],
        "technologies": ["Python", "FastAPI", "Docker"],
        "interests": ["Robotique"],
    }
    data.update(overrides)
    return json.dumps(data)
