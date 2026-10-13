import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
)

from app.schemas.common import dedupe

ContractType = Literal["internship", "apprenticeship", "full_time", "part_time", "contract"]
Place = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]

ContractTypes = Annotated[list[ContractType], Field(max_length=5), AfterValidator(dedupe)]
Places = Annotated[list[Place], Field(max_length=20), AfterValidator(dedupe)]


class PreferencesUpdate(BaseModel):
    """Remplacement complet des préférences."""

    model_config = ConfigDict(extra="forbid")

    contract_types: ContractTypes = Field(default_factory=list)
    locations: Places = Field(default_factory=list)
    domains: Places = Field(default_factory=list)
    remote_ok: bool = False
    willing_to_relocate: bool = False


class PreferencesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None
    contract_types: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    remote_ok: bool = False
    willing_to_relocate: bool = False
    updated_at: datetime | None = None
