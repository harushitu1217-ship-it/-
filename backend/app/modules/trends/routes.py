from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import TrendSource, User
from app.db.session import get_db
from app.modules.auth.routes import get_current_user, require_roles
from app.modules.trends.schemas import TrendImport, TrendPublic
from app.modules.trends.service import import_trend, seed_public_trends

router = APIRouter(prefix="/api/trends", tags=["trends"])


def trend_public(item: TrendSource) -> TrendPublic:
    return TrendPublic.model_validate(item, from_attributes=True)


@router.get("")
def list_trends(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    rows = db.scalars(select(TrendSource).order_by(TrendSource.updated_at.desc())).all()
    return {"items": [trend_public(item) for item in rows]}


@router.post("/import", response_model=TrendPublic, status_code=status.HTTP_201_CREATED)
def add_trend(
    request: TrendImport,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "operator")),
) -> TrendPublic:
    return trend_public(import_trend(db, request))


@router.post("/seed-public")
def add_public_seeds(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))) -> dict:
    return {"imported": seed_public_trends(db)}


@router.post("/{trend_id}/archive")
def archive_trend(
    trend_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "operator")),
) -> dict:
    trend = db.get(TrendSource, trend_id)
    if trend is None:
        raise HTTPException(status_code=404, detail="热点模板不存在")
    trend.archived = True
    db.commit()
    return {"id": trend.id, "archived": True}
