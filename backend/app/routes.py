from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from app.database import open_connection
from app.generator import generate_contents, generate_contents_with_ai
from app.models import AiConfig, GenerationTask, ImageAsset, PlatformAuthConfig
from app.platform_auth import (
    PLATFORM_AUTH_PROVIDERS,
    known_platform_auth_configs,
    public_platform_auth_config,
    start_platform_auth,
)
from app.repository import (
    get_ai_config,
    get_platform_auth_config,
    list_history,
    list_platform_auth_configs,
    save_ai_config,
    save_generated_contents,
    save_platform_auth_config,
)
from app.seed_data import DEFAULT_COMPANY_PROFILE, DEFAULT_PLATFORM_TEMPLATES, DEFAULT_PRODUCTS

PUBLISH_LINKS = {
    "xiaohongshu": "https://creator.xiaohongshu.com/",
    "douyin": "https://creator.douyin.com/",
    "kuaishou": "https://cp.kuaishou.com/",
    "toutiao": "https://mp.toutiao.com/",
    "shipinhao": "https://channels.weixin.qq.com/",
    "wechat": "https://mp.weixin.qq.com/",
}


class GenerateRequest(BaseModel):
    product_name: str
    content_type: str
    platforms: list[str]
    selling_points: str = ""
    image_assets: list[dict] = []


class AiConfigRequest(BaseModel):
    api_url: str
    api_key: str
    model: str


class PlatformAuthConfigRequest(BaseModel):
    platform: str
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str] = []
    auth_url_template: str = ""


def _public_ai_config(config: AiConfig | None) -> dict:
    if config is None or not config.is_complete:
        return {
            "configured": False,
            "api_url": "",
            "model": "",
            "api_key_hint": "",
        }
    return {
        "configured": True,
        "api_url": config.api_url,
        "model": config.model,
        "api_key_hint": "已保存",
    }


def _image_assets_from_request(raw_assets: list[dict]) -> list[ImageAsset]:
    return [
        ImageAsset(
            id=str(asset.get("id", "")),
            url=str(asset.get("url", "")),
            original_name=str(asset.get("original_name", "")),
            content_type=str(asset.get("content_type", "")),
        )
        for asset in raw_assets
        if asset.get("id") and asset.get("url")
    ]


def create_router(db_path: str | None = None, ai_generator=generate_contents_with_ai) -> APIRouter:
    router = APIRouter()
    upload_root = Path(__file__).resolve().parents[2] / "data" / "uploads"

    @router.get("/api/bootstrap")
    def bootstrap() -> dict:
        return {
            "company": asdict(DEFAULT_COMPANY_PROFILE),
            "products": [asdict(product) for product in DEFAULT_PRODUCTS],
            "templates": [asdict(template) for template in DEFAULT_PLATFORM_TEMPLATES],
            "publish_links": PUBLISH_LINKS,
        }

    @router.post("/api/assets/images")
    async def upload_image_asset(file: UploadFile) -> dict:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="只支持上传图片文件")
        suffix = Path(file.filename or "image").suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            suffix = ".jpg"
        upload_root.mkdir(parents=True, exist_ok=True)
        asset_id = f"{uuid4().hex}{suffix}"
        target = upload_root / asset_id
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="图片文件不能为空")
        target.write_bytes(content)
        return asdict(
            ImageAsset(
                id=asset_id,
                url=f"/uploads/{asset_id}",
                original_name=file.filename or asset_id,
                content_type=file.content_type,
            )
        )

    @router.get("/api/ai-config")
    def load_ai_config() -> dict:
        with open_connection(db_path) as conn:
            from app.database import initialize_database

            initialize_database(conn)
            return _public_ai_config(get_ai_config(conn))

    @router.post("/api/ai-config")
    def update_ai_config(request: AiConfigRequest) -> dict:
        config = AiConfig(api_url=request.api_url, api_key=request.api_key, model=request.model)
        if not config.is_complete:
            raise HTTPException(status_code=422, detail="API 地址、API Key 和模型名称都要填写")
        with open_connection(db_path) as conn:
            from app.database import initialize_database

            initialize_database(conn)
            save_ai_config(conn, config)
        return _public_ai_config(config)

    @router.post("/api/generate")
    def generate(request: GenerateRequest) -> dict:
        if request.content_type not in {"lead", "education", "product_intro"}:
            raise HTTPException(status_code=422, detail="content_type must be lead, education or product_intro")

        task = GenerationTask(
            product_name=request.product_name,
            content_type=request.content_type,  # type: ignore[arg-type]
            platforms=request.platforms,
            selling_points=request.selling_points,
            image_assets=_image_assets_from_request(request.image_assets),
        )

        try:
            with open_connection(db_path) as conn:
                from app.database import initialize_database

                initialize_database(conn)
                config = get_ai_config(conn)

            if config is None or not config.is_complete:
                contents = generate_contents(task, DEFAULT_COMPANY_PROFILE, DEFAULT_PRODUCTS, DEFAULT_PLATFORM_TEMPLATES)
            else:
                try:
                    contents = ai_generator(task, config, DEFAULT_COMPANY_PROFILE, DEFAULT_PRODUCTS, DEFAULT_PLATFORM_TEMPLATES)
                except ValueError as exc:
                    raise HTTPException(status_code=502, detail=f"AI API 调用失败：{exc}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        with open_connection(db_path) as conn:
            from app.database import initialize_database

            initialize_database(conn)
            save_generated_contents(conn, task, contents)
        return {"contents": [asdict(item) for item in contents]}

    @router.get("/api/history")
    def history() -> dict:
        with open_connection(db_path) as conn:
            from app.database import initialize_database

            initialize_database(conn)
            return {"items": list_history(conn)}

    @router.get("/api/publish-links")
    def publish_links() -> dict:
        return {"links": PUBLISH_LINKS}

    @router.get("/api/platform-auth/configs")
    def platform_auth_configs() -> dict:
        with open_connection(db_path) as conn:
            from app.database import initialize_database

            initialize_database(conn)
            saved = list_platform_auth_configs(conn)
        return {"items": known_platform_auth_configs(saved)}

    @router.post("/api/platform-auth/configs")
    def update_platform_auth_config(request: PlatformAuthConfigRequest) -> dict:
        if request.platform not in PLATFORM_AUTH_PROVIDERS:
            raise HTTPException(status_code=422, detail="暂不支持这个平台")
        config = PlatformAuthConfig(
            platform=request.platform,
            client_id=request.client_id,
            client_secret=request.client_secret,
            redirect_uri=request.redirect_uri,
            scopes=request.scopes,
            auth_url_template=request.auth_url_template,
        )
        if not config.is_complete:
            raise HTTPException(status_code=422, detail="平台、App ID、App Secret 和回调地址都要填写")
        with open_connection(db_path) as conn:
            from app.database import initialize_database

            initialize_database(conn)
            save_platform_auth_config(conn, config)
        return public_platform_auth_config(config)

    @router.post("/api/platform-auth/{platform}/start")
    def start_auth(platform: str) -> dict:
        if platform not in PLATFORM_AUTH_PROVIDERS:
            raise HTTPException(status_code=422, detail="暂不支持这个平台")
        with open_connection(db_path) as conn:
            from app.database import initialize_database

            initialize_database(conn)
            config = get_platform_auth_config(conn, platform)
        return start_platform_auth(config, platform)

    @router.get("/api/platform-auth/{platform}/callback")
    def platform_auth_callback(platform: str, code: str = "", state: str = "") -> dict:
        if platform not in PLATFORM_AUTH_PROVIDERS:
            raise HTTPException(status_code=422, detail="暂不支持这个平台")
        return {
            "platform": platform,
            "status": "received_code" if code else "missing_code",
            "code_received": bool(code),
            "state": state,
            "message": "已收到授权回调。下一版会在这里用 code 换 access_token 并保存发布凭证。",
        }

    return router
