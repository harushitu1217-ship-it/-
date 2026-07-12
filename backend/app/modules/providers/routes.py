from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import ModelConfig, User
from app.db.session import get_db
from app.modules.auth.routes import require_roles
from app.modules.providers.crypto import SecretCipher

PROVIDER_DEFAULTS = {
    "doubao": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
    "deepseek": "https://api.deepseek.com/chat/completions",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
}

router = APIRouter(prefix="/api/settings", tags=["providers"])


class ModelConfigInput(BaseModel):
    provider: str
    api_url: str = ""
    api_key: str = ""
    model: str = Field(min_length=1, max_length=160)
    priority: int = Field(default=100, ge=1, le=1000)
    enabled: bool = True


def public_config(config: ModelConfig) -> dict:
    return {
        "provider": config.provider,
        "api_url": config.api_url,
        "model": config.model,
        "priority": config.priority,
        "enabled": config.enabled,
        "configured": bool(config.api_key_encrypted),
        "api_key_hint": "已保存" if config.api_key_encrypted else "",
    }


@router.get("/models")
def list_model_configs(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))) -> dict:
    saved = {item.provider: item for item in db.scalars(select(ModelConfig).order_by(ModelConfig.priority))}
    items = []
    for provider, default_url in PROVIDER_DEFAULTS.items():
        config = saved.get(provider)
        items.append(public_config(config) if config else {"provider": provider, "api_url": default_url, "model": "", "priority": 100, "enabled": False, "configured": False, "api_key_hint": ""})
    return {"items": items}


@router.put("/models/{provider}")
def save_model_config(
    provider: str,
    request: ModelConfigInput,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: User = Depends(require_roles("admin")),
) -> dict:
    if provider not in PROVIDER_DEFAULTS or request.provider != provider:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="不支持的模型供应商")
    config = db.scalar(select(ModelConfig).where(ModelConfig.provider == provider))
    if config is None:
        config = ModelConfig(provider=provider, api_url=request.api_url or PROVIDER_DEFAULTS[provider], model=request.model)
        db.add(config)
    config.api_url = request.api_url or PROVIDER_DEFAULTS[provider]
    config.model = request.model
    config.priority = request.priority
    config.enabled = request.enabled
    if request.api_key:
        config.api_key_encrypted = SecretCipher(settings.jwt_secret).encrypt(request.api_key)
    db.commit()
    db.refresh(config)
    return public_config(config)
