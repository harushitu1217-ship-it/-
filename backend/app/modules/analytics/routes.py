from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import PublishTask, User
from app.db.session import get_db
from app.modules.analytics.schemas import ManualMetrics
from app.modules.analytics.service import metrics_summary, save_manual_metrics
from app.modules.auth.routes import get_current_user, require_roles

router = APIRouter(prefix="/api", tags=["analytics"])


@router.post("/publish-tasks/{task_id}/metrics", status_code=status.HTTP_201_CREATED)
def add_metrics(
    task_id: str,
    request: ManualMetrics,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "operator", "reviewer")),
) -> dict:
    task = db.get(PublishTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="发布任务不存在")
    saved = save_manual_metrics(db, task, request, user)
    return {"task_id": saved.id, **saved.metrics}


@router.get("/analytics/summary")
def summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    return metrics_summary(db)
