from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ContentJob, ContentVersion, PublishTask

PUBLISH_URLS = {
    "xiaohongshu": "https://creator.xiaohongshu.com/",
    "douyin": "https://creator.douyin.com/",
    "kuaishou": "https://cp.kuaishou.com/",
    "toutiao": "https://mp.toutiao.com/",
    "shipinhao": "https://channels.weixin.qq.com/",
    "wechat": "https://mp.weixin.qq.com/",
}
MAX_PUBLISH_RETRIES = 3


def latest_platform_version(db: Session, job_id: str, platform: str) -> ContentVersion | None:
    return db.scalar(
        select(ContentVersion)
        .where(ContentVersion.job_id == job_id, ContentVersion.platform == platform)
        .order_by(ContentVersion.version_number.desc(), ContentVersion.created_at.desc())
        .limit(1)
    )


def create_publish_task(db: Session, job: ContentJob, platform: str) -> PublishTask:
    if job.status != "approved":
        raise ValueError("只有审核通过的内容可以创建发布任务")
    if platform not in job.platforms or platform not in PUBLISH_URLS:
        raise ValueError("该平台不在内容任务中")
    version = latest_platform_version(db, job.id, platform)
    if version is None:
        raise ValueError("该平台没有可发布的内容版本")
    task = PublishTask(
        content_version_id=version.id,
        platform=platform,
        mode="manual",
        status="ready_for_manual_publish",
        retry_count=0,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def manual_publish_package(db: Session, task: PublishTask) -> dict:
    version = db.get(ContentVersion, task.content_version_id)
    if version is None:
        raise ValueError("发布内容版本不存在")
    payload = version.payload or {}
    return {
        "task_id": task.id,
        "platform": task.platform,
        "title": version.title,
        "body": version.body,
        "tags": payload.get("tags", []),
        "keywords": payload.get("keywords", []),
        "image_suggestions": payload.get("image_suggestions", []),
        "publish_tip": payload.get("publish_tip", ""),
        "publish_url": PUBLISH_URLS[task.platform],
    }


def record_publish_failure(db: Session, task: PublishTask, error_code: str) -> PublishTask:
    task.retry_count += 1
    task.status = "failed" if task.retry_count >= MAX_PUBLISH_RETRIES else "queued"
    task.metrics = {**(task.metrics or {}), "last_error_code": error_code}
    db.commit()
    db.refresh(task)
    return task
