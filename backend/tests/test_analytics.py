from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base, ContentJob, ContentVersion, ProductRow, PublishTask, User
from app.modules.analytics.schemas import ManualMetrics
from app.modules.analytics.service import save_manual_metrics


def test_manual_metrics_are_attributed_to_publish_task():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(username="operator", password_hash="hash", role="operator")
        product = ProductRow(name="织带")
        db.add_all([user, product])
        db.flush()
        job = ContentJob(created_by_id=user.id, product_id=product.id, status="approved", platforms=["xiaohongshu"])
        db.add(job)
        db.flush()
        version = ContentVersion(job_id=job.id, platform="xiaohongshu", version_number=1, title="标题", body="正文", payload={}, created_by_id=user.id)
        db.add(version)
        db.flush()
        task = PublishTask(content_version_id=version.id, platform="xiaohongshu", mode="manual", status="published")
        db.add(task)
        db.commit()

        save_manual_metrics(db, task, ManualMetrics(views=1200, likes=38, favorites=12, inquiries=3), user)

    assert task.metrics["inquiries"] == 3

