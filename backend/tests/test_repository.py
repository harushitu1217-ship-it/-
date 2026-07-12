from app.database import connect, initialize_database
from app.generator import generate_contents
from app.models import GenerationTask
from app.models import AiConfig
from app.repository import get_ai_config, list_history, save_ai_config, save_generated_contents
from app.seed_data import DEFAULT_COMPANY_PROFILE, DEFAULT_PLATFORM_TEMPLATES, DEFAULT_PRODUCTS


def test_save_and_list_generated_history(tmp_path):
    db_path = tmp_path / "test.db"
    conn = connect(str(db_path))
    initialize_database(conn)
    task = GenerationTask("鞋带", "lead", ["douyin"], "适合鞋帽客户批量定制")
    contents = generate_contents(task, DEFAULT_COMPANY_PROFILE, DEFAULT_PRODUCTS, DEFAULT_PLATFORM_TEMPLATES)

    save_generated_contents(conn, task, contents)
    history = list_history(conn)

    assert len(history) == 1
    assert history[0]["product_name"] == "鞋带"
    assert history[0]["platform"] == "douyin"
    assert "明景绳带有限公司" in history[0]["body"]


def test_save_and_get_ai_config_masks_api_key(tmp_path):
    db_path = tmp_path / "test.db"
    conn = connect(str(db_path))
    initialize_database(conn)

    save_ai_config(
        conn,
        AiConfig(
            api_url="https://api.example.com/v1/chat/completions",
            api_key="sk-test-secret",
            model="gpt-test",
        ),
    )

    config = get_ai_config(conn)

    assert config is not None
    assert config.api_url == "https://api.example.com/v1/chat/completions"
    assert config.api_key == "sk-test-secret"
    assert config.model == "gpt-test"
