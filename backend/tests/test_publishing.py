from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base, ContentJob, ContentVersion, ProductRow, User
from app.modules.publishing.service import create_publish_task, manual_publish_package


def test_unconfigured_platform_creates_manual_package():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        reviewer = User(username="reviewer", password_hash="hash", role="reviewer")
        product = ProductRow(name="织带")
        db.add_all([reviewer, product])
        db.flush()
        job = ContentJob(created_by_id=reviewer.id, product_id=product.id, status="approved", platforms=["xiaohongshu"])
        db.add(job)
        db.flush()
        version = ContentVersion(job_id=job.id, platform="xiaohongshu", version_number=1, title="织带采购避坑", body="正文内容", payload={"tags": ["织带厂家"]}, created_by_id=reviewer.id)
        db.add(version)
        db.commit()

        task = create_publish_task(db, job, "xiaohongshu")
        package = manual_publish_package(db, task)

    assert task.mode == "manual"
    assert task.status == "ready_for_manual_publish"
    assert package["title"] == "织带采购避坑"
    assert package["tags"] == ["织带厂家"]
    assert package["publish_url"].startswith("https://")
