from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from app.modules.content.schemas import Platform


class TrendImport(BaseModel):
    platform: Platform
    source_url: HttpUrl | None = None
    source_text: str = Field(min_length=20, max_length=30000)
    expires_at: datetime | None = None


class TrendPublic(BaseModel):
    id: str
    platform: str
    source_url: str | None
    source_text: str
    structure_summary: dict
    expires_at: datetime | None
    archived: bool
    created_at: datetime
    updated_at: datetime
