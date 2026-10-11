import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from app.schemas.common import dedupe

ShortText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]
Tag = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
]
PartialDate = Annotated[str, StringConstraints(strip_whitespace=True, max_length=20)]
TagList = Annotated[list[Tag], Field(max_length=100), AfterValidator(dedupe)]


class EducationItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    school: ShortText
    degree: ShortText | None = None
    field_of_study: ShortText | None = None
    start_year: int | None = Field(default=None, ge=1950, le=2100)
    end_year: int | None = Field(default=None, ge=1950, le=2100)

    @model_validator(mode="after")
    def check_years(self) -> Self:
        if self.start_year and self.end_year and self.end_year < self.start_year:
            raise ValueError("end_year must not be before start_year")
        return self


class ExperienceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: ShortText
    title: ShortText
    start: PartialDate | None = None  # « 2024 » ou « 2024-06 » : dates partielles
    end: PartialDate | None = None  # vide = en cours
    description: LongText | None = None
    technologies: Annotated[list[Tag], Field(max_length=30)] = Field(
        default_factory=list
    )


class ProfileUpdate(BaseModel):
    """Modification partielle : seuls les champs envoyés sont changés."""

    model_config = ConfigDict(extra="forbid")

    summary: LongText | None = None
    objectives: LongText | None = None
    education: Annotated[list[EducationItem], Field(max_length=20)] | None = None
    experiences: Annotated[list[ExperienceItem], Field(max_length=30)] | None = None
    skills: TagList | None = None
    technologies: TagList | None = None
    interests: TagList | None = None


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version: int
    is_current: bool
    cv_id: uuid.UUID | None
    source: str
    extraction_model: str | None
    summary: str | None
    objectives: str | None
    education: list[EducationItem]
    experiences: list[ExperienceItem]
    skills: list[str]
    technologies: list[str]
    interests: list[str]
    created_at: datetime
    updated_at: datetime