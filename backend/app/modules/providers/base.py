from typing import Any, Protocol

from pydantic import BaseModel, Field


class ModelRequest(BaseModel):
    messages: list[dict[str, Any]]
    temperature: float = Field(default=0.6, ge=0, le=2)
    response_format: dict[str, Any] | None = None


class ModelResponse(BaseModel):
    provider: str
    model: str
    text: str
    raw: dict[str, Any]


class ModelProvider(Protocol):
    name: str

    def generate(self, request: ModelRequest) -> ModelResponse: ...


class ImageAnalysisRequest(BaseModel):
    image_urls: list[str]
    prompt: str


class ImageAnalysis(BaseModel):
    facts: dict[str, str]
    needs_confirmation: list[str]
    confidence: float = Field(ge=0, le=1)


class ImageGenerationRequest(BaseModel):
    prompt: str
    aspect_ratio: str = "3:4"


class GeneratedImage(BaseModel):
    provider: str
    url: str


class ImageProvider(Protocol):
    name: str

    def analyze(self, request: ImageAnalysisRequest) -> ImageAnalysis: ...
    def generate(self, request: ImageGenerationRequest) -> GeneratedImage: ...


class UnconfiguredImageProvider:
    name = "unconfigured"

    def analyze(self, request: ImageAnalysisRequest) -> ImageAnalysis:
        raise RuntimeError("provider_not_configured")

    def generate(self, request: ImageGenerationRequest) -> GeneratedImage:
        raise RuntimeError("provider_not_configured")
