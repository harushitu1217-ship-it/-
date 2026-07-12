from sqlalchemy import create_engine, inspect

from app.db.models import Base


def test_initial_schema_contains_core_tables(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'schema.db'}")

    Base.metadata.create_all(engine)

    table_names = set(inspect(engine).get_table_names())
    assert {
        "users",
        "company_profiles",
        "products",
        "assets",
        "model_configs",
        "content_jobs",
        "content_versions",
        "publish_tasks",
        "trend_sources",
        "audit_logs",
    } <= table_names
