from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CompanyProfileRow, ContentJob, ContentVersion, ProductRow, User
from app.modules.audit.service import record_audit
from app.generator import generate_contents
from app.models import GenerationTask, Product
from app.modules.content.quality import quality_issues
from app.modules.content.schemas import ContentJobCreate
from app.modules.trends.service import select_trend_context
from app.seed_data import DEFAULT_COMPANY_PROFILE, DEFAULT_PLATFORM_TEMPLATES


def create_content_job(db: Session, user: User, request: ContentJobCreate) -> ContentJob:
    if db.get(ProductRow, request.product_id) is None:
        raise ValueError("产品不存在")
    platforms = list(dict.fromkeys(request.platforms))
    job = ContentJob(
        created_by_id=user.id,
        product_id=request.product_id,
        status="draft",
        requirements=request.requirements,
        platforms=platforms,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def list_versions(db: Session, job_id: str) -> list[ContentVersion]:
    versions = list(db.scalars(select(ContentVersion).where(ContentVersion.job_id == job_id)))
    job = db.get(ContentJob, job_id)
    platform_order = {platform: index for index, platform in enumerate(job.platforms if job else [])}
    return sorted(versions, key=lambda item: (platform_order.get(item.platform, 999), item.version_number, item.created_at, item.id))


def _generator_product(row: ProductRow) -> Product:
    return Product(
        name=row.name,
        aliases=row.aliases or [],
        materials=row.materials or [],
        uses=row.uses or [],
        industries=row.industries or [],
        questions=row.questions or [],
    )


def generate_content_job(db: Session, job: ContentJob, user: User) -> ContentJob:
    if job.status not in {"draft", "changes_requested", "failed"}:
        raise ValueError("当前状态不能生成内容")
    product = db.get(ProductRow, job.product_id)
    if product is None:
        raise ValueError("产品不存在")
    job.status = "generating"
    job.error_message = None
    db.commit()
    try:
        task = GenerationTask(
            product_name=product.name,
            content_type="product_intro",
            platforms=list(job.platforms),
            selling_points=job.requirements,
        )
        generated = generate_contents(task, DEFAULT_COMPANY_PROFILE, [_generator_product(product)], DEFAULT_PLATFORM_TEMPLATES)
        profile = db.scalar(select(CompanyProfileRow).limit(1))
        previous = list_versions(db, job.id)
        next_versions = {item.platform: item.version_number + 1 for item in previous}
        for item in generated:
            issues = quality_issues(item.title, item.body, profile)
            trend_sources = [
                {"id": trend.id, "source_url": trend.source_url, "structure_summary": trend.structure_summary}
                for trend in select_trend_context(db, item.platform)
            ]
            version = ContentVersion(
                job_id=job.id,
                platform=item.platform,
                version_number=next_versions.get(item.platform, 1),
                title=item.title,
                body=item.body,
                payload={
                    "tags": item.tags,
                    "keywords": item.keywords,
                    "image_suggestions": item.image_suggestions,
                    "publish_tip": item.publish_tip,
                    "optional_script": item.optional_script,
                    "quality_issues": issues,
                    "trend_sources": trend_sources,
                },
                created_by_id=user.id,
            )
            db.add(version)
        job.status = "pending_review"
        db.commit()
        db.refresh(job)
        return job
    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        db.commit()
        raise


def update_content_version(db: Session, version: ContentVersion, user: User, title: str, body: str, payload: dict) -> ContentVersion:
    job = db.get(ContentJob, version.job_id)
    if job is None or job.status not in {"pending_review", "changes_requested"}:
        raise ValueError("当前状态不能修改内容")
    new_version = ContentVersion(
        job_id=version.job_id,
        platform=version.platform,
        version_number=version.version_number + 1,
        title=title,
        body=body,
        payload=payload,
        created_by_id=user.id,
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)
    return new_version


def review_content_job(db: Session, job: ContentJob, reviewer: User, decision: str, comment: str) -> ContentJob:
    if reviewer.role not in {"admin", "reviewer"}:
        raise ValueError("只有管理员或审核员可以审核")
    if job.status != "pending_review":
        raise ValueError("当前状态不能审核")
    if decision not in {"approved", "changes_requested"}:
        raise ValueError("审核决定无效")
    job.status = decision
    if comment:
        job.error_message = comment if decision == "changes_requested" else None
    record_audit(
        db,
        reviewer.id,
        f"content.{decision}",
        "content_job",
        job.id,
        {"comment": comment},
    )
    db.commit()
    db.refresh(job)
    return job
