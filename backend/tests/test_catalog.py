from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base
from app.modules.catalog.schemas import ProductCreate
from app.modules.catalog.service import create_product, list_products


def test_product_can_be_created_and_listed():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        created = create_product(
            db,
            ProductCreate(
                name="涤纶织带",
                aliases=["箱包织带"],
                materials=["涤纶"],
                uses=["箱包肩带"],
                industries=["箱包"],
                questions=["可以来样定制吗"],
            ),
        )
        products = list_products(db)

    assert created.name == "涤纶织带"
    assert [item.name for item in products] == ["涤纶织带"]

