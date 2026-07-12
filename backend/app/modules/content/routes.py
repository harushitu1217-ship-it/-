from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ContentJob, ContentVersion, User
from app.db.session import get_db
from app.modules.auth.routes import get_current_user, require_roles
from app.modules.content.schemas import ContentJobCreate, ContentVersionUpdate, ReviewRequest
from app.modules.content.service import (
    create_content_job,
    generate_content_job,
    list_versions,
    review_content_job,
    update_content_version,
)

router = APIRouter(prefix="/api", tags=["content"])


def version_public(version: ContentVersion) -> dict:
    return {
        "id": version.id,
        "platform": version.platform,
        "version_number": version.version_number,
        "title": version.title,
        "body": version.body,
        "payload": version.payload,
    }


def job_public(db: Session, job: ContentJob) -> dict:
    return {
        "id": job.id,
        "product_id": job.product_id,
        "status": job.status,
        "requirements": job.requirements,
        "platforms": job.platforms,
        "error_message": job.error_message,
        "versions": [version_public(item) for item in list_versions(db, job.id)],
    }


@router.post("/content-jobs", status_code=status.HTTP_201_CREATED)
def add_content_job(
    request: ContentJobCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "operator")),
) -> dict:
    try:
        return job_public(db, create_content_job(db, user, request))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/content-jobs")
def content_jobs(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    jobs = db.scalars(select(ContentJob).order_by(ContentJob.created_at.desc())).all()
    return {"items": [job_public(db, item) for item in jobs]}


@router.post("/content-jobs/{job_id}/generate")
def generate_job(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "operator")),
) -> dict:
    job = db.get(ContentJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="内容任务不存在")
    try:
        return job_public(db, generate_content_job(db, job, user))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/content-versions/{version_id}")
def edit_version(
    version_id: str,
    request: ContentVersionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "operator")),
) -> dict:
    version = db.get(ContentVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="内容版本不存在")
    try:
        return version_public(update_content_version(db, version, user, request.title, request.body, request.payload))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/content-jobs/{job_id}/submit")
def submit_job(
    job_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "operator")),
) -> dict:
    job = db.get(ContentJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="内容任务不存在")
    if job.status == "changes_requested":
        job.status = "pending_review"
        db.commit()
    elif job.status != "pending_review":
        raise HTTPException(status_code=409, detail="当前状态不能提交审核")
    return job_public(db, job)


@router.post("/content-jobs/{job_id}/review")
def review_job(
    job_id: str,
    request: ReviewRequest,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_roles("admin", "reviewer")),
) -> dict:
    job = db.get(ContentJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="内容任务不存在")
    try:
        return job_public(db, review_content_job(db, job, reviewer, request.decision, request.comment))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
