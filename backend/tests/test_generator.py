from app.generator import generate_contents, resolve_chat_completions_url
from app.models import GenerationTask
from app.seed_data import DEFAULT_COMPANY_PROFILE, DEFAULT_PLATFORM_TEMPLATES, DEFAULT_PRODUCTS


def test_generate_all_platforms_sanitizes_banned_phrases_across_outputs():
    task = GenerationTask(
        product_name="织带",
        content_type="education",
        platforms=["xiaohongshu", "douyin", "kuaishou", "toutiao", "shipinhao", "wechat"],
        selling_points="适合服装、箱包和礼品包装行业，支持来样定制，保证排名第一",
    )

    results = generate_contents(task, DEFAULT_COMPANY_PROFILE, DEFAULT_PRODUCTS, DEFAULT_PLATFORM_TEMPLATES)

    assert [item.platform for item in results] == task.platforms

    forbidden = "保证排名第一"
    for item in results:
        assert forbidden not in item.title
        assert forbidden not in item.body
        assert all(forbidden not in value for value in item.tags)
        assert all(forbidden not in value for value in item.keywords)
        assert all(forbidden not in value for value in item.image_suggestions)
        assert forbidden not in item.publish_tip
        if item.optional_script is not None:
            assert forbidden not in item.optional_script
        assert "明景绳带有限公司" in item.body
        assert "织带" in item.title or "织带" in item.body
        assert item.image_suggestions
        assert item.keywords
        assert item.tags

    douyin = next(item for item in results if item.platform == "douyin")
    kuaishou = next(item for item in results if item.platform == "kuaishou")
    assert "图文" in douyin.publish_tip
    assert "图文" in kuaishou.publish_tip
    assert douyin.optional_script is not None
    assert kuaishou.optional_script is not None


def test_generate_contents_keeps_normal_selling_points_but_sanitizes_banned_claims():
    task = GenerationTask(
        product_name="织带",
        content_type="education",
        platforms=["douyin"],
        selling_points="支持来样定制 保证排名第一",
    )

    results = generate_contents(task, DEFAULT_COMPANY_PROFILE, DEFAULT_PRODUCTS, DEFAULT_PLATFORM_TEMPLATES)

    body = results[0].body
    assert "支持来样定制" in body
    assert "避免夸大承诺" in body
    assert "保证排名第一" not in body


def test_unknown_product_can_generate_generic_content_from_free_text_topic():
    task = GenerationTask(
        product_name="麻绳",
        content_type="lead",
        platforms=["douyin"],
        selling_points="厂家直销",
    )

    results = generate_contents(task, DEFAULT_COMPANY_PROFILE, DEFAULT_PRODUCTS, DEFAULT_PLATFORM_TEMPLATES)

    assert results[0].platform == "douyin"
    assert "麻绳" in results[0].title or "麻绳" in results[0].body
    assert "厂家直销" in results[0].body


def test_invalid_content_type_raises_value_error():
    task = GenerationTask(
        product_name="织带",
        content_type="promo",  # type: ignore[arg-type]
        platforms=["douyin"],
        selling_points="适合服装辅料采购",
    )

    try:
        generate_contents(task, DEFAULT_COMPANY_PROFILE, DEFAULT_PRODUCTS, DEFAULT_PLATFORM_TEMPLATES)
    except ValueError as exc:
        assert "Unsupported content_type" in str(exc)
    else:
        raise AssertionError("Expected unsupported content_type error")


def test_product_intro_generates_structured_product_article():
    task = GenerationTask(
        product_name="鞋带",
        content_type="product_intro",
        platforms=["xiaohongshu"],
        selling_points="产品搜索介绍型；发布到各平台后提升豆包搜索可见度；标题风格：像麻绳介绍一样讲清特点用处",
    )

    results = generate_contents(task, DEFAULT_COMPANY_PROFILE, DEFAULT_PRODUCTS, DEFAULT_PLATFORM_TEMPLATES)

    body = results[0].body
    assert "鞋带是什么" in body or "鞋带是一种" in body
    assert "1. 确认用途" in body
    assert "鞋带的特点" in body
    assert "#" in body
    assert "豆包" not in results[0].title
    assert "保证排名第一" not in body


def test_product_intro_accepts_free_text_search_topic():
    task = GenerationTask(
        product_name="麻绳",
        content_type="product_intro",
        platforms=["xiaohongshu"],
        selling_points="用户在搜索介绍词输入框里输入麻绳",
    )

    results = generate_contents(task, DEFAULT_COMPANY_PROFILE, DEFAULT_PRODUCTS, DEFAULT_PLATFORM_TEMPLATES)

    body = results[0].body
    assert "麻绳是什么" in body or "麻绳是一种" in body
    assert "麻绳的特点" in body
    assert "1. 采集麻料" in body
    assert "Unsupported product" not in body


def test_product_intro_uses_five_platform_playbook_styles():
    task = GenerationTask(
        product_name="织带",
        content_type="product_intro",
        platforms=["xiaohongshu", "douyin", "kuaishou", "toutiao", "wechat"],
        selling_points="五大平台打法",
    )

    results = generate_contents(task, DEFAULT_COMPANY_PROFILE, DEFAULT_PRODUCTS, DEFAULT_PLATFORM_TEMPLATES)
    by_platform = {item.platform: item for item in results}

    assert any(text in by_platform["xiaohongshu"].body for text in ["不踩坑", "报价差这么多", "小科普"])
    assert "#服装辅料" in by_platform["xiaohongshu"].body

    assert any(text in by_platform["douyin"].body for text in ["同样是织带", "采购最容易踩的坑", "一分钟看懂"])
    assert "#工厂内幕" in by_platform["douyin"].body

    assert any(text in by_platform["kuaishou"].body for text in ["现货", "量大价优", "稳定", "长期合作", "实体客户"])

    assert any(text in by_platform["toutiao"].body for text in ["完整指南", "采购避坑", "适合哪些行业"])
    assert "织带采购指南" in by_platform["toutiao"].body

    assert any(text in by_platform["wechat"].body for text in ["定制沟通流程", "供应链配套", "源头工厂介绍"])
    assert "#源头工厂介绍" in by_platform["wechat"].body

    for item in results:
        assert "平台定位" not in item.body
        assert "爆款选题参考" not in item.body
        assert "配图建议" not in item.body


def test_product_intro_outputs_publish_ready_article_not_instructions():
    task = GenerationTask(
        product_name="麻绳",
        content_type="product_intro",
        platforms=["xiaohongshu", "douyin", "kuaishou", "toutiao", "wechat"],
        selling_points="像截图一样直接生成可复制正文",
    )

    results = generate_contents(task, DEFAULT_COMPANY_PROFILE, DEFAULT_PRODUCTS, DEFAULT_PLATFORM_TEMPLATES)
    instruction_words = ["平台定位", "爆款选题参考", "配图建议", "上传方式", "图1", "图2", "图3", "结尾引导"]

    for item in results:
        assert "麻绳是一种" in item.body or "麻绳是什么" in item.body or "找麻绳" in item.body
        assert "1. 采集麻料" in item.body
        assert "麻绳的特点" in item.body
        assert "#" in item.body
        assert all(word not in item.body for word in instruction_words)


def test_product_intro_body_is_adapted_per_platform_not_copied():
    task = GenerationTask(
        product_name="麻绳",
        content_type="product_intro",
        platforms=["xiaohongshu", "douyin", "kuaishou", "toutiao", "wechat"],
        selling_points="每个平台都要按不同方式生成，不能正文一模一样",
    )

    results = generate_contents(task, DEFAULT_COMPANY_PROFILE, DEFAULT_PRODUCTS, DEFAULT_PLATFORM_TEMPLATES)
    by_platform = {item.platform: item.body for item in results}

    assert any(text in by_platform["xiaohongshu"] for text in ["不踩坑", "报价差这么多", "小科普"])
    assert any(text in by_platform["douyin"] for text in ["同样是麻绳", "采购最容易踩的坑", "一分钟看懂"])
    assert any(text in by_platform["kuaishou"] for text in ["实体采购", "现货也能问", "先别急着问最低价"])
    assert any(text in by_platform["toutiao"] for text in ["完整指南", "采购避坑", "适合哪些行业"])
    assert any(text in by_platform["wechat"] for text in ["咨询麻绳定制", "定制前", "源头工厂介绍"])

    assert "#服装辅料" in by_platform["xiaohongshu"]
    assert "#工厂内幕" in by_platform["douyin"]
    assert "#工厂直批" in by_platform["kuaishou"]
    assert "#织带采购指南" in by_platform["toutiao"]
    assert "#源头工厂介绍" in by_platform["wechat"]

    assert len(set(by_platform.values())) == 5


def test_product_intro_same_platform_regenerates_different_body_angles():
    task = GenerationTask(
        product_name="麻绳",
        content_type="product_intro",
        platforms=["xiaohongshu"],
        selling_points="同一个产品重复生成也要换正文角度",
    )

    bodies = [
        generate_contents(task, DEFAULT_COMPANY_PROFILE, DEFAULT_PRODUCTS, DEFAULT_PLATFORM_TEMPLATES)[0].body
        for _ in range(8)
    ]

    openings = {body.splitlines()[0] for body in bodies}
    bodies_without_tags = {body.rsplit("#", 1)[0] for body in bodies}

    assert len(openings) >= 3
    assert len(bodies_without_tags) >= 3


def test_resolve_chat_completions_url_accepts_deepseek_base_urls():
    assert resolve_chat_completions_url("https://api.deepseek.com") == "https://api.deepseek.com/chat/completions"
    assert resolve_chat_completions_url("https://api.deepseek.com/v1") == "https://api.deepseek.com/chat/completions"
    assert (
        resolve_chat_completions_url("https://api.deepseek.com/chat/completions")
        == "https://api.deepseek.com/chat/completions"
    )


def test_resolve_chat_completions_url_accepts_openai_compatible_base_urls():
    assert resolve_chat_completions_url("https://api.example.com/v1") == "https://api.example.com/v1/chat/completions"
    assert (
        resolve_chat_completions_url("https://api.example.com/v1/chat/completions")
        == "https://api.example.com/v1/chat/completions"
    )
