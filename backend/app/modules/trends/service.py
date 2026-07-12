from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import TrendSource
from app.modules.trends.schemas import TrendImport


def summarize_structure(text: str) -> dict:
    normalized = text.strip()
    hooks = []
    for name, markers in {
        "用途反差": ("竟然", "意外用途", "没想到"),
        "清单科普": ("一口气", "多种", "清单"),
        "问题解答": ("为什么", "怎么", "如何"),
        "过程记录": ("变化", "过程", "从打样到"),
        "避坑采购": ("避坑", "采购", "注意"),
    }.items():
        if any(marker in normalized for marker in markers):
            hooks.append(name)
    return {
        "hook_types": hooks or ["信息说明"],
        "recommended_sections": ["标题钩子", "产品事实", "应用场景", "采购建议", "咨询引导"],
        "copy_policy": "只参考结构，不复制原句",
    }


def import_trend(db: Session, request: TrendImport) -> TrendSource:
    source_url = str(request.source_url) if request.source_url else None
    trend = db.scalar(select(TrendSource).where(TrendSource.source_url == source_url)) if source_url else None
    if trend is None:
        trend = TrendSource(platform=request.platform, source_url=source_url, source_text=request.source_text)
        db.add(trend)
    trend.platform = request.platform
    trend.source_text = request.source_text.strip()
    trend.structure_summary = summarize_structure(request.source_text)
    trend.expires_at = request.expires_at
    trend.archived = False
    db.commit()
    db.refresh(trend)
    return trend


def _is_not_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return True
    value = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=UTC)
    return value > datetime.now(UTC)


def select_trend_context(db: Session, platform: str, limit: int = 5) -> list[TrendSource]:
    rows = db.scalars(
        select(TrendSource)
        .where(TrendSource.platform == platform, TrendSource.archived.is_(False), or_(TrendSource.expires_at.is_(None), TrendSource.expires_at > datetime.utcnow()))
        .order_by(TrendSource.updated_at.desc())
        .limit(limit)
    ).all()
    return [item for item in rows if _is_not_expired(item.expires_at)]


PUBLIC_TREND_SEEDS = [
    TrendImport(platform="xiaohongshu", source_url="https://www.xiaohongshu.com/explore", source_text="公开发现页结构观察：用途反差、为什么类问题、一口气认识多种、时间变化记录。用于绳带内容时转化为材料用途、采购问答、材质清单和打样过程。"),
    TrendImport(platform="douyin", source_url="https://www.douyin.com/hot", source_text="抖音公开热榜和规则入口：适合结论前置、问题钩子、过程展示和短句信息密度结构，不复制具体热榜内容。"),
    TrendImport(platform="kuaishou", source_url="https://www.kuaishou.com/brilliant", source_text="快手公开内容入口：使用真实工厂、现货、打样、发货过程和直接问答结构，强调可验证的生产信息。"),
    TrendImport(platform="toutiao", source_url="https://www.toutiao.com/", source_text="今日头条公开信息流：采用完整问题标题、采购指南、材料对比、分段解释和延伸问题结构。"),
    TrendImport(platform="shipinhao", source_url="https://channels.weixin.qq.com/", source_text="视频号公开入口：采用口播开场、产品应用、工厂过程、朋友圈转发摘要和私域咨询结构。"),
    TrendImport(platform="wechat", source_url="https://mp.weixin.qq.com/", source_text="公众号公开平台入口：采用导语、目录、材料知识、采购步骤、案例说明和结尾咨询结构。"),
]


def seed_public_trends(db: Session) -> int:
    for request in PUBLIC_TREND_SEEDS:
        import_trend(db, request)
    return len(PUBLIC_TREND_SEEDS)
