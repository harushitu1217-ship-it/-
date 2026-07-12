from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PublishTask, User
from app.modules.analytics.schemas import ManualMetrics
from app.modules.audit.service import record_audit


def save_manual_metrics(db: Session, task: PublishTask, metrics: ManualMetrics, user: User) -> PublishTask:
    task.metrics = metrics.model_dump()
    record_audit(db, user.id, "publish.metrics_updated", "publish_task", task.id, task.metrics)
    db.commit()
    db.refresh(task)
    return task


def metrics_summary(db: Session) -> dict:
    totals = {"views": 0, "likes": 0, "favorites": 0, "inquiries": 0, "published_tasks": 0}
    for task in db.scalars(select(PublishTask)).all():
        if task.status == "published":
            totals["published_tasks"] += 1
        for key in ("views", "likes", "favorites", "inquiries"):
            totals[key] += int((task.metrics or {}).get(key, 0))
    return totals
