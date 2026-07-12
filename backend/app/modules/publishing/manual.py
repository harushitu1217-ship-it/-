from app.modules.publishing.base import PublishResult


class ManualPublisher:
    def __init__(self, platform: str):
        self.platform = platform

    def publish(self, package: dict) -> PublishResult:
        return PublishResult(status="ready_for_manual_publish")
