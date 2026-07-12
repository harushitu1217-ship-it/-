from typing import Literal

from pydantic import BaseModel, Field

Platform = Literal["xiaohongshu", "douyin", "kuaishou", "toutiao", "shipinhao", "wechat"]


class ContentJobCreate(BaseModel):
    product_id: str
    requirements: str = Field(default="", max_length=10000)
    platforms: list[Platform] = Field(min_length=1)
    content_type: Literal["lead", "education", "product_intro"] = "product_intro"


class ContentVersionUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1, max_length=50000)
    payload: dict = {}


class ReviewRequest(BaseModel):
    decision: Literal["approved", "changes_requested"]
    comment: str = Field(default="", max_length=2000)


class ImageAnalysisPublic(BaseModel):
    facts: dict[str, str]
    needs_confirmation: list[str]
    confidence: float
