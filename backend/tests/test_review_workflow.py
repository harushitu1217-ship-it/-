import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base, ContentJob, ProductRow, User
from app.modules.content.service import review_content_job


def test_draft_job_cannot_be_approved():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        reviewer = User(username="reviewer", password_hash="hash", role="reviewer")
        operator = User(username="operator", password_hash="hash", role="operator")
        product = ProductRow(name="织带")
        db.add_all([reviewer, operator, product])
        db.flush()
        job = ContentJob(created_by_id=operator.id, product_id=product.id, status="draft", platforms=["xiaohongshu"])
        db.add(job)
        db.commit()

        with pytest.raises(ValueError, match="当前状态不能审核"):
            review_content_job(db, job, reviewer, "approved", "")
