import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CVRead(BaseModel):
    """Public view of a CV. `storage_path` and `extracted_text` are never exposed."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    content_type: str
    file_size_bytes: int
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime
