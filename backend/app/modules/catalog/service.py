from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CompanyProfileRow, ProductRow
from app.modules.catalog.schemas import CompanyProfileUpdate, ProductCreate

ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_JOB_IMAGES = 9


def validate_image_upload(original_name: str, content_type: str, content: bytes) -> str:
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("只支持 JPEG、PNG 和 WebP 图片")
    if not content:
        raise ValueError("图片文件不能为空")
    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError("单张图片不能超过 10 MiB")
    return ALLOWED_IMAGE_TYPES[content_type]


def create_product(db: Session, request: ProductCreate) -> ProductRow:
    product = ProductRow(**request.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def list_products(db: Session) -> list[ProductRow]:
    return list(db.scalars(select(ProductRow).order_by(ProductRow.created_at, ProductRow.name)))


def update_product(db: Session, product: ProductRow, request: ProductCreate) -> ProductRow:
    for key, value in request.model_dump().items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def get_or_create_company_profile(db: Session) -> CompanyProfileRow:
    profile = db.scalar(select(CompanyProfileRow).limit(1))
    if profile is None:
        profile = CompanyProfileRow(name="明景绳带有限公司")
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def update_company_profile(db: Session, request: CompanyProfileUpdate) -> CompanyProfileRow:
    profile = get_or_create_company_profile(db)
    for key, value in request.model_dump().items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


def remove_storage_file(storage_root: Path, storage_key: str) -> None:
    target = (storage_root / storage_key).resolve()
    root = storage_root.resolve()
    if root not in target.parents:
        raise ValueError("素材路径无效")
    target.unlink(missing_ok=True)
