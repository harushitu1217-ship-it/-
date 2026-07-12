from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict

from fastapi.testclient import TestClient

from app.generator import generate_contents
from app.main import create_app


def test_health_endpoint(tmp_path):
    app = create_app(str(tmp_path / "api.db"))
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_endpoint_uses_local_templates_without_ai_config(tmp_path):
    app = create_app(str(tmp_path / "api.db"))
    client = TestClient(app)

    response = client.post(
        "/api/generate",
        json={
            "product_name": "帽绳",
            "content_type": "education",
            "platforms": ["douyin", "kuaishou"],
            "selling_points": "颜色规格齐全，可打样",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert [item["platform"] for item in data["contents"]] == ["douyin", "kuaishou"]
    assert "帽绳" in data["contents"][0]["title"] or "帽绳" in data["contents"][0]["body"]


def test_ai_config_can_be_saved_and_loaded_without_exposing_key(tmp_path):
    app = create_app(str(tmp_path / "api.db"))
    client = TestClient(app)

    save_response = client.post(
        "/api/ai-config",
        json={
            "api_url": "https://api.example.com/v1/chat/completions",
            "api_key": "sk-test-secret",
            "model": "gpt-test",
        },
    )

    assert save_response.status_code == 200
    assert save_response.json() == {
        "configured": True,
        "api_url": "https://api.example.com/v1/chat/completions",
        "model": "gpt-test",
        "api_key_hint": "已保存",
    }

    load_response = client.get("/api/ai-config")

    assert load_response.status_code == 200
    assert load_response.json() == {
        "configured": True,
        "api_url": "https://api.example.com/v1/chat/completions",
        "model": "gpt-test",
        "api_key_hint": "已保存",
    }


def test_upload_image_asset_returns_preview_url(tmp_path):
    app = create_app(str(tmp_path / "api.db"))
    client = TestClient(app)

    response = client.post(
        "/api/assets/images",
        files={"file": ("sample.png", b"\x89PNG\r\n\x1a\nsample", "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"].endswith(".png")
    assert data["original_name"] == "sample.png"
    assert data["content_type"] == "image/png"
    assert data["url"].startswith("/uploads/")

    preview = client.get(data["url"])
    assert preview.status_code == 200
    assert preview.content == b"\x89PNG\r\n\x1a\nsample"


def test_generate_endpoint_uses_configured_ai_client(tmp_path):
    captured = {}

    def fake_generate_with_ai(task, config, profile, products, templates):
        captured["api_url"] = config.api_url
        captured["model"] = config.model
        captured["image_assets"] = [asdict(asset) for asset in task.image_assets]
        return generate_contents(task, profile, products, templates)

    app = create_app(str(tmp_path / "api.db"), ai_generator=fake_generate_with_ai)
    client = TestClient(app)

    client.post(
        "/api/ai-config",
        json={
            "api_url": "https://api.example.com/v1/chat/completions",
            "api_key": "sk-test-secret",
            "model": "gpt-test",
        },
    )

    response = client.post(
        "/api/generate",
        json={
            "product_name": "帽绳",
            "content_type": "education",
            "platforms": ["douyin", "kuaishou"],
            "selling_points": "颜色规格齐全，可打样",
            "image_assets": [
                {
                    "id": "asset-1.png",
                    "url": "/uploads/asset-1.png",
                    "original_name": "asset.png",
                    "content_type": "image/png",
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert [item["platform"] for item in data["contents"]] == ["douyin", "kuaishou"]
    assert data["contents"][0]["image_suggestions"]
    assert "图文" in data["contents"][0]["publish_tip"]
    assert captured == {
        "api_url": "https://api.example.com/v1/chat/completions",
        "model": "gpt-test",
        "image_assets": [
            {
                "id": "asset-1.png",
                "url": "/uploads/asset-1.png",
                "original_name": "asset.png",
                "content_type": "image/png",
            }
        ],
    }
    assert data["contents"][0]["image_assets"][0]["url"] == "/uploads/asset-1.png"


def test_product_intro_uses_configured_ai_client_when_available(tmp_path):
    captured = {}

    def fake_generate_with_ai(task, config, profile, products, templates):
        captured["content_type"] = task.content_type
        captured["product_name"] = task.product_name
        captured["api_url"] = config.api_url
        return generate_contents(task, profile, products, templates)

    app = create_app(str(tmp_path / "api.db"), ai_generator=fake_generate_with_ai)
    client = TestClient(app)
    client.post(
        "/api/ai-config",
        json={
            "api_url": "https://api.deepseek.com",
            "api_key": "sk-test-secret",
            "model": "deepseek-chat",
        },
    )

    response = client.post(
        "/api/generate",
        json={
            "product_name": "麻绳",
            "content_type": "product_intro",
            "platforms": ["xiaohongshu"],
            "selling_points": "有 API 时必须调用 AI",
        },
    )

    assert response.status_code == 200
    assert captured == {
        "content_type": "product_intro",
        "product_name": "麻绳",
        "api_url": "https://api.deepseek.com",
    }


def test_configured_ai_failure_returns_error_instead_of_template_fallback(tmp_path):
    def failing_generate_with_ai(task, config, profile, products, templates):
        raise ValueError("DeepSeek 返回 401，请检查 API Key")

    app = create_app(str(tmp_path / "api.db"), ai_generator=failing_generate_with_ai)
    client = TestClient(app)
    client.post(
        "/api/ai-config",
        json={
            "api_url": "https://api.deepseek.com",
            "api_key": "bad-key",
            "model": "deepseek-chat",
        },
    )

    response = client.post(
        "/api/generate",
        json={
            "product_name": "麻绳",
            "content_type": "product_intro",
            "platforms": ["xiaohongshu"],
            "selling_points": "不能偷偷用固定模板",
        },
    )

    assert response.status_code == 502
    assert "AI API 调用失败" in response.json()["detail"]
    assert "DeepSeek 返回 401" in response.json()["detail"]


def test_publish_links_are_available(tmp_path):
    app = create_app(str(tmp_path / "api.db"))
    client = TestClient(app)

    response = client.get("/api/publish-links")

    assert response.status_code == 200
    links = response.json()["links"]
    assert links["douyin"].startswith("https://")
    assert links["wechat"].startswith("https://")


def test_platform_auth_config_can_be_saved_without_exposing_secret(tmp_path):
    app = create_app(str(tmp_path / "api.db"))
    client = TestClient(app)

    response = client.post(
        "/api/platform-auth/configs",
        json={
            "platform": "douyin",
            "client_id": "douyin-client",
            "client_secret": "douyin-secret",
            "redirect_uri": "https://example.com/callback/douyin",
            "scopes": ["video.create", "user_info"],
        },
    )

    assert response.status_code == 200
    saved = response.json()
    assert saved["platform"] == "douyin"
    assert saved["client_id"] == "douyin-client"
    assert saved["configured"] is True
    assert saved["client_secret_hint"] == "已保存"
    assert saved["redirect_uri"] == "https://example.com/callback/douyin"
    assert saved["scopes"] == ["video.create", "user_info"]
    assert saved["auth_url_template"] == ""
    assert saved["developer_portal_url"].startswith("https://")
    assert saved["setup_steps"]

    configs = client.get("/api/platform-auth/configs")

    assert configs.status_code == 200
    data = configs.json()["items"]
    douyin = next(item for item in data if item["platform"] == "douyin")
    assert douyin["configured"] is True
    assert douyin["client_secret_hint"] == "已保存"
    assert "douyin-secret" not in str(data)


def test_platform_auth_start_returns_authorize_url_and_qr_svg(tmp_path):
    app = create_app(str(tmp_path / "api.db"))
    client = TestClient(app)
    client.post(
        "/api/platform-auth/configs",
        json={
            "platform": "douyin",
            "client_id": "douyin-client",
            "client_secret": "douyin-secret",
            "redirect_uri": "https://example.com/callback/douyin",
            "scopes": ["video.create", "user_info"],
        },
    )

    response = client.post("/api/platform-auth/douyin/start")

    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "douyin"
    assert data["status"] == "ready"
    assert data["authorize_url"].startswith("https://open.douyin.com/")
    assert "client_key=douyin-client" in data["authorize_url"]
    assert "redirect_uri=https%3A%2F%2Fexample.com%2Fcallback%2Fdouyin" in data["authorize_url"]
    assert data["qr_svg"].startswith("data:image/svg+xml;base64,")
    assert data["callback_url"] == "https://example.com/callback/douyin"


def test_platform_auth_start_explains_missing_official_access(tmp_path):
    app = create_app(str(tmp_path / "api.db"))
    client = TestClient(app)

    response = client.post("/api/platform-auth/xiaohongshu/start")

    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "xiaohongshu"
    assert data["status"] == "needs_config"
    assert data["qr_svg"] == ""
    assert data["developer_portal_url"].startswith("https://")
    assert data["setup_steps"]
    assert "开放平台" in data["message"]


def test_multiple_generate_calls_accumulate_history_after_ai_config(tmp_path):
    def fake_generate_with_ai(task, config, profile, products, templates):
        return generate_contents(task, profile, products, templates)

    app = create_app(str(tmp_path / "api.db"), ai_generator=fake_generate_with_ai)
    client = TestClient(app)

    client.post(
        "/api/ai-config",
        json={
            "api_url": "https://api.example.com/v1/chat/completions",
            "api_key": "sk-test-secret",
            "model": "gpt-test",
        },
    )

    payloads = [
        {
            "product_name": "帽绳",
            "content_type": "lead",
            "platforms": ["douyin"],
            "selling_points": "A",
        },
        {
            "product_name": "织带",
            "content_type": "education",
            "platforms": ["kuaishou"],
            "selling_points": "B",
        },
        {
            "product_name": "鞋带",
            "content_type": "lead",
            "platforms": ["wechat"],
            "selling_points": "C",
        },
    ]

    def submit(payload: dict) -> int:
        response = client.post("/api/generate", json=payload)
        assert response.status_code == 200
        return response.status_code

    with ThreadPoolExecutor(max_workers=3) as executor:
        statuses = list(executor.map(submit, payloads))

    assert statuses == [200, 200, 200]

    history = client.get("/api/history")
    assert history.status_code == 200
    items = history.json()["items"]
    assert len(items) == 3
    assert {item["product_name"] for item in items} == {"帽绳", "织带", "鞋带"}
