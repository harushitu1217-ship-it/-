from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models import AuditLog, Base, ContentJob, ProductRow, User
from app.modules.content.service import review_content_job


def test_review_action_creates_audit_event():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        reviewer = User(username="reviewer", password_hash="hash", role="reviewer")
        operator = User(username="operator", password_hash="hash", role="operator")
        product = ProductRow(name="织带")
        db.add_all([reviewer, operator, product])
        db.flush()
        job = ContentJob(created_by_id=operator.id, product_id=product.id, status="pending_review", platforms=["xiaohongshu"])
        db.add(job)
        db.commit()

        review_content_job(db, job, reviewer, "approved", "内容真实")
        event = db.scalar(select(AuditLog).where(AuditLog.entity_id == job.id, AuditLog.action == "content.approved"))

    assert event is not None
    assert "api_key" not in str(event.details).lower()
