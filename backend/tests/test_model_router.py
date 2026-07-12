from app.modules.providers.base import ModelRequest, ModelResponse
from app.modules.providers.router import ModelRouter


class FailingProvider:
    name = "doubao"

    def generate(self, request: ModelRequest) -> ModelResponse:
        raise RuntimeError("temporary failure")


class StubProvider:
    name = "deepseek"

    def generate(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(provider=self.name, model="deepseek-chat", text="ok", raw={})


def test_router_falls_back_in_configured_order():
    router = ModelRouter([FailingProvider(), StubProvider()])

    result = router.generate(ModelRequest(messages=[{"role": "user", "content": "test"}]))

    assert result.provider == "deepseek"
    assert result.text == "ok"

