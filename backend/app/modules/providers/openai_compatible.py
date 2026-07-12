import httpx

from app.modules.providers.base import ModelRequest, ModelResponse


class OpenAICompatibleProvider:
    def __init__(self, name: str, api_url: str, api_key: str, model: str, timeout_seconds: float = 60.0):
        self.name = name
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, request: ModelRequest) -> ModelResponse:
        payload = {"model": self.model, "messages": request.messages, "temperature": request.temperature}
        if request.response_format:
            payload["response_format"] = request.response_format
        response = httpx.post(
            self.api_url,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        raw = response.json()
        text = str(raw["choices"][0]["message"]["content"])
        return ModelResponse(provider=self.name, model=self.model, text=text, raw=raw)
