from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BytesIO
from urllib.parse import urlencode

import qrcode
import qrcode.image.svg

from app.models import PlatformAuthConfig


@dataclass(frozen=True)
class PlatformAuthProvider:
    platform: str
    name: str
    authorize_base_url: str
    client_id_param: str
    scope_separator: str = ","
    default_scopes: tuple[str, ...] = ()
    notes: str = ""
    developer_portal_url: str = ""
    setup_steps: tuple[str, ...] = ()


PLATFORM_AUTH_PROVIDERS: dict[str, PlatformAuthProvider] = {
    "douyin": PlatformAuthProvider(
        platform="douyin",
        name="抖音图文",
        authorize_base_url="https://open.douyin.com/platform/oauth/connect/",
        client_id_param="client_key",
        default_scopes=("user_info", "video.create"),
        notes="需要先在抖音开放平台创建应用，并申请内容发布相关权限。",
        developer_portal_url="https://developer.open-douyin.com/",
        setup_steps=("注册或登录抖音开放平台", "创建应用并配置回调地址", "申请内容发布相关权限", "把 App ID 和 App Secret 填回本系统"),
    ),
    "kuaishou": PlatformAuthProvider(
        platform="kuaishou",
        name="快手图文",
        authorize_base_url="https://open.kuaishou.com/oauth2/authorize",
        client_id_param="app_id",
        default_scopes=("user_info",),
        notes="需要先在快手开放平台创建应用，并申请对应发布权限。",
        developer_portal_url="https://open.kuaishou.com/",
        setup_steps=("注册或登录快手开放平台", "创建应用并配置 OAuth 回调地址", "申请图文或内容发布权限", "把 App ID 和 App Secret 填回本系统"),
    ),
    "toutiao": PlatformAuthProvider(
        platform="toutiao",
        name="今日头条",
        authorize_base_url="https://open.snssdk.com/oauth/authorize",
        client_id_param="client_key",
        default_scopes=("user_info",),
        notes="头条号发布能力需要按官方开放平台权限申请。",
        developer_portal_url="https://developer.open-douyin.com/",
        setup_steps=("登录字节开放平台", "确认头条号内容发布能力", "创建应用并配置回调地址", "把应用参数填回本系统"),
    ),
    "wechat": PlatformAuthProvider(
        platform="wechat",
        name="公众号",
        authorize_base_url="https://mp.weixin.qq.com/cgi-bin/componentloginpage",
        client_id_param="component_appid",
        default_scopes=(),
        notes="公众号通常走微信第三方平台授权，需要 component_appid、预授权码等官方流程。",
        developer_portal_url="https://open.weixin.qq.com/",
        setup_steps=("注册微信开放平台第三方平台", "绑定公众号相关能力", "配置授权回调域名", "把官方参数填回本系统"),
    ),
    "shipinhao": PlatformAuthProvider(
        platform="shipinhao",
        name="视频号",
        authorize_base_url="https://mp.weixin.qq.com/cgi-bin/componentloginpage",
        client_id_param="component_appid",
        default_scopes=(),
        notes="视频号能力依赖微信生态官方授权，部分发布能力可能需要人工确认。",
        developer_portal_url="https://channels.weixin.qq.com/",
        setup_steps=("登录视频号助手", "确认账号主体和发布权限", "按微信生态开放能力配置授权", "无法开放的动作保留人工确认"),
    ),
    "xiaohongshu": PlatformAuthProvider(
        platform="xiaohongshu",
        name="小红书",
        authorize_base_url="https://open.xiaohongshu.com/oauth/authorize",
        client_id_param="client_id",
        default_scopes=("user_info",),
        notes="小红书内容发布接口需要官方开放平台或服务商权限。",
        developer_portal_url="https://www.xiaohongshu.com/",
        setup_steps=("联系小红书开放平台或服务商", "确认内容发布接口权限", "获取应用参数", "配置回调地址并填回本系统"),
    ),
}


def public_platform_auth_config(config: PlatformAuthConfig) -> dict:
    provider = PLATFORM_AUTH_PROVIDERS[config.platform]
    return {
        "platform": config.platform,
        "client_id": config.client_id,
        "configured": config.is_complete,
        "client_secret_hint": "已保存" if config.client_secret else "",
        "redirect_uri": config.redirect_uri,
        "scopes": config.scopes,
        "auth_url_template": config.auth_url_template,
        "developer_portal_url": provider.developer_portal_url,
        "setup_steps": list(provider.setup_steps),
    }


def known_platform_auth_configs(saved: list[PlatformAuthConfig]) -> list[dict]:
    by_platform = {item.platform: item for item in saved}
    items = []
    for platform, provider in PLATFORM_AUTH_PROVIDERS.items():
        config = by_platform.get(platform)
        if config:
            items.append(public_platform_auth_config(config))
        else:
            items.append(
                {
                    "platform": platform,
                    "client_id": "",
                    "configured": False,
                    "client_secret_hint": "",
                    "redirect_uri": "",
                    "scopes": list(provider.default_scopes),
                    "auth_url_template": "",
                    "developer_portal_url": provider.developer_portal_url,
                    "setup_steps": list(provider.setup_steps),
                }
            )
    return items


def build_authorize_url(config: PlatformAuthConfig) -> str:
    provider = PLATFORM_AUTH_PROVIDERS[config.platform]
    scopes = config.scopes or list(provider.default_scopes)
    if config.auth_url_template.strip():
        return (
            config.auth_url_template.strip()
            .replace("{client_id}", config.client_id)
            .replace("{redirect_uri}", config.redirect_uri)
            .replace("{scope}", provider.scope_separator.join(scopes))
        )
    query = {
        provider.client_id_param: config.client_id,
        "redirect_uri": config.redirect_uri,
        "response_type": "code",
        "scope": provider.scope_separator.join(scopes),
        "state": f"mingjing-{config.platform}",
    }
    return f"{provider.authorize_base_url}?{urlencode(query)}"


def qr_svg_data_uri(value: str) -> str:
    image = qrcode.make(value, image_factory=qrcode.image.svg.SvgImage)
    output = BytesIO()
    image.save(output)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def start_platform_auth(config: PlatformAuthConfig | None, platform: str) -> dict:
    provider = PLATFORM_AUTH_PROVIDERS[platform]
    if config is None or not config.is_complete:
        return {
            "platform": platform,
            "status": "needs_config",
            "authorize_url": "",
            "qr_svg": "",
            "callback_url": "",
            "message": f"{provider.name}需要先在开放平台申请应用，填写 App ID、App Secret 和回调地址后才能生成扫码授权。",
            "notes": provider.notes,
            "developer_portal_url": provider.developer_portal_url,
            "setup_steps": list(provider.setup_steps),
        }
    authorize_url = build_authorize_url(config)
    return {
        "platform": platform,
        "status": "ready",
        "authorize_url": authorize_url,
        "qr_svg": qr_svg_data_uri(authorize_url),
        "callback_url": config.redirect_uri,
        "message": "请用对应平台账号扫码或打开授权链接完成授权。",
        "notes": provider.notes,
        "developer_portal_url": provider.developer_portal_url,
        "setup_steps": list(provider.setup_steps),
    }
