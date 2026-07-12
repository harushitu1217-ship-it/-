from app.db.models import CompanyProfileRow

AD_LAW_RISK_PHRASES = {"行业第一", "绝对最好", "100%保证", "保证排名第一"}


def quality_issues(title: str, body: str, profile: CompanyProfileRow | None) -> list[str]:
    text = f"{title}\n{body}"
    banned = set(profile.banned_phrases if profile else []) | AD_LAW_RISK_PHRASES
    return [f"包含禁用表达：{phrase}" for phrase in sorted(banned) if phrase and phrase in text]
