from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ContentJob, PublishTask, User
from app.db.session import get_db
from app.modules.auth.routes import get_current_user, require_roles
from app.modules.publishing.service import create_publish_task, manual_publish_package

router = APIRouter(prefix="/api", tags=["publishing"])


class CreatePublishTaskRequest(BaseModel):
    platform: str


def task_public(task: PublishTask) -> dict:
    return {
        "id": task.id,
        "content_version_id": task.content_version_id,
        "platform": task.platform,
        "mode": task.mode,
        "status": task.status,
        "scheduled_at": task.scheduled_at,
        "retry_count": task.retry_count,
        "external_id": task.external_id,
        "metrics": task.metrics,
    }


@router.post("/content-jobs/{job_id}/publish-tasks", status_code=status.HTTP_201_CREATED)
def add_publish_task(
    job_id: str,
    request: CreatePublishTaskRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "reviewer")),
) -> dict:
    job = db.get(ContentJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="内容任务不存在")
    try:
        return task_public(create_publish_task(db, job, request.platform))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/publish-tasks")
def publish_tasks(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    rows = db.scalars(select(PublishTask).order_by(PublishTask.created_at.desc())).all()
    return {"items": [task_public(item) for item in rows]}


@router.get("/publish-tasks/{task_id}/package")
def publish_package(task_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    task = db.get(PublishTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="发布任务不存在")
    try:
        return manual_publish_package(db, task)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/publish-tasks/{task_id}/mark-published")
def mark_published(
    task_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "operator", "reviewer")),
) -> dict:
    task = db.get(PublishTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="发布任务不存在")
    task.status = "published"
    db.commit()
    db.refresh(task)
    return task_public(task)
