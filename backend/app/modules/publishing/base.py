from typing import Literal, Protocol

from pydantic import BaseModel


class PublishResult(BaseModel):
    status: Literal["published", "ready_for_manual_publish", "failed"]
    external_id: str | None = None
    error_code: str | None = None


class PlatformPublisher(Protocol):
    platform: str

    def publish(self, package: dict) -> PublishResult: ...
