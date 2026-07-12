from app.modules.providers.base import ModelProvider, ModelRequest, ModelResponse


class ModelRouter:
    def __init__(self, providers: list[ModelProvider]):
        self.providers = providers

    def generate(self, request: ModelRequest) -> ModelResponse:
        errors: list[str] = []
        for provider in self.providers:
            try:
                return provider.generate(request)
            except Exception as exc:
                errors.append(f"{provider.name}: {exc}")
        if not self.providers:
            raise RuntimeError("没有配置可用的 AI 模型")
        raise RuntimeError("所有 AI 模型调用失败：" + "; ".join(errors))
