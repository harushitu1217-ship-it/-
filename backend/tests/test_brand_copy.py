from app.main import create_app
from app.seed_data import DEFAULT_COMPANY_PROFILE


def test_application_uses_mingjing_brand():
    app = create_app()

    assert app.title == "明景内容运营助手"
    assert DEFAULT_COMPANY_PROFILE.name.startswith("明景")
    assert "明璟" not in DEFAULT_COMPANY_PROFILE.name
