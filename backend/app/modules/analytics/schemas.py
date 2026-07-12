from pydantic import BaseModel, Field


class ManualMetrics(BaseModel):
    views: int = Field(default=0, ge=0)
    likes: int = Field(default=0, ge=0)
    favorites: int = Field(default=0, ge=0)
    inquiries: int = Field(default=0, ge=0)
