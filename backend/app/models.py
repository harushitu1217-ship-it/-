from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ContentType = Literal["lead", "education", "product_intro"]


@dataclass(frozen=True)
class CompanyProfile:
    name: str
    summary: str
    advantages: list[str]
    industries: list[str]
    contact_note: str
    banned_phrases: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Product:
    name: str
    aliases: list[str]
    materials: list[str]
    uses: list[str]
    industries: list[str]
    questions: list[str]


@dataclass(frozen=True)
class PlatformTemplate:
    platform: str
    label: str
    title_pattern: str
    body_sections: list[str]
    tag_prefixes: list[str]
    publish_tip: str
    supports_optional_script: bool = False


@dataclass(frozen=True)
class ImageAsset:
    id: str
    url: str
    original_name: str
    content_type: str


@dataclass(frozen=True)
class GenerationTask:
    product_name: str
    content_type: ContentType
    platforms: list[str]
    selling_points: str = ""
    image_assets: list[ImageAsset] = field(default_factory=list)


@dataclass(frozen=True)
class AiConfig:
    api_url: str
    api_key: str
    model: str

    @property
    def is_complete(self) -> bool:
        return bool(self.api_url.strip() and self.api_key.strip() and self.model.strip())


@dataclass(frozen=True)
class PlatformAuthConfig:
    platform: str
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str] = field(default_factory=list)
    auth_url_template: str = ""

    @property
    def is_complete(self) -> bool:
        return bool(self.platform.strip() and self.client_id.strip() and self.client_secret.strip() and self.redirect_uri.strip())


@dataclass(frozen=True)
class GeneratedContent:
    platform: str
    title: str
    body: str
    tags: list[str]
    keywords: list[str]
    image_suggestions: list[str]
    publish_tip: str
    optional_script: str | None = None
    image_assets: list[ImageAsset] = field(default_factory=list)
