from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base, ProductRow, User
from app.modules.content.schemas import ContentJobCreate
from app.modules.content.service import create_content_job, generate_content_job, list_versions


def test_generated_job_is_waiting_for_review_and_platforms_differ():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(username="operator", password_hash="hash", role="operator")
        product = ProductRow(name="涤纶织带", materials=["涤纶"], uses=["箱包肩带"])
        db.add_all([user, product])
        db.commit()
        job = create_content_job(
            db,
            user,
            ContentJobCreate(product_id=product.id, requirements="强调来样定制", platforms=["xiaohongshu", "wechat"]),
        )

        generate_content_job(db, job, user)
        versions = list_versions(db, job.id)

    assert job.status == "pending_review"
    assert [item.platform for item in versions] == ["xiaohongshu", "wechat"]
    assert versions[0].body != versions[1].body

