from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base
from app.modules.trends.schemas import TrendImport
from app.modules.trends.service import import_trend, select_trend_context


def test_duplicate_source_url_updates_existing_trend():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        first = import_trend(db, TrendImport(platform="xiaohongshu", source_url="https://example.com/a", source_text="用途反差标题结构，先提出意外用途，再解释产品细节。"))
        second = import_trend(db, TrendImport(platform="xiaohongshu", source_url="https://example.com/a", source_text="更新后的用途反差结构，增加采购场景和避坑说明。"))

    assert second.id == first.id
    assert "更新后" in second.source_text


def test_expired_trend_is_not_selected():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        import_trend(db, TrendImport(platform="douyin", source_text="当前可用的热榜问答结构，先给结论再展示过程。"))
        import_trend(db, TrendImport(platform="douyin", source_text="这是一条已经过期的模板内容，不应该进入后续的生成上下文。", expires_at=datetime.now(UTC) - timedelta(days=1)))
        selected = select_trend_context(db, "douyin")

    assert len(selected) == 1
    assert "当前可用" in selected[0].source_text
