from pydantic import BaseModel, Field


class CompanyProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    summary: str = Field(default="", max_length=5000)
    advantages: list[str] = []
    industries: list[str] = []
    contact_note: str = Field(default="", max_length=2000)
    banned_phrases: list[str] = []


class CompanyProfilePublic(CompanyProfileUpdate):
    id: str


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    aliases: list[str] = []
    materials: list[str] = []
    uses: list[str] = []
    industries: list[str] = []
    questions: list[str] = []


class ProductPublic(ProductCreate):
    id: str


class AssetPublic(BaseModel):
    id: str
    url: str
    original_name: str
    content_type: str
    size_bytes: int
    product_id: str | None = None
