"""Schema sent to the LLM (structured output).

Deliberately plain: no validators and no length constraints, because the Gemini API only
supports a subset of JSON Schema. The strict validation is done afterwards with
`app.schemas.profile.ProfileUpdate`.
"""

from pydantic import BaseModel


class EducationOut(BaseModel):
    school: str
    degree: str | None
    field_of_study: str | None
    start_year: int | None
    end_year: int | None


class ExperienceOut(BaseModel):
    company: str
    title: str
    start: str | None
    end: str | None
    description: str | None
    technologies: list[str]


class ProfileExtraction(BaseModel):
    summary: str | None
    objectives: str | None
    education: list[EducationOut]
    experiences: list[ExperienceOut]
    skills: list[str]
    technologies: list[str]
    interests: list[str]
