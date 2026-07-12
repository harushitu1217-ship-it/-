from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import Asset, ProductRow, User
from app.db.session import get_db
from app.modules.auth.routes import get_current_user, require_roles
from app.modules.catalog.schemas import (
    AssetPublic,
    CompanyProfilePublic,
    CompanyProfileUpdate,
    ProductCreate,
    ProductPublic,
)
from app.modules.catalog.service import (
    create_product,
    get_or_create_company_profile,
    list_products,
    remove_storage_file,
    update_company_profile,
    update_product,
    validate_image_upload,
)

router = APIRouter(prefix="/api", tags=["catalog"])


def product_public(product: ProductRow) -> ProductPublic:
    return ProductPublic.model_validate(product, from_attributes=True)


def asset_public(asset: Asset) -> AssetPublic:
    return AssetPublic(
        id=asset.id,
        url=f"/uploads/{asset.storage_key}",
        original_name=asset.original_name,
        content_type=asset.content_type,
        size_bytes=asset.size_bytes,
        product_id=asset.product_id,
    )


@router.get("/company-profile", response_model=CompanyProfilePublic)
def company_profile(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> CompanyProfilePublic:
    return CompanyProfilePublic.model_validate(get_or_create_company_profile(db), from_attributes=True)


@router.put("/company-profile", response_model=CompanyProfilePublic)
def save_company_profile(
    request: CompanyProfileUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> CompanyProfilePublic:
    return CompanyProfilePublic.model_validate(update_company_profile(db, request), from_attributes=True)


@router.get("/products", response_model=list[ProductPublic])
def products(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[ProductPublic]:
    return [product_public(item) for item in list_products(db)]


@router.post("/products", response_model=ProductPublic, status_code=status.HTTP_201_CREATED)
def add_product(
    request: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "operator")),
) -> ProductPublic:
    return product_public(create_product(db, request))


@router.put("/products/{product_id}", response_model=ProductPublic)
def save_product(
    product_id: str,
    request: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "operator")),
) -> ProductPublic:
    product = db.get(ProductRow, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="产品不存在")
    return product_public(update_product(db, product, request))


@router.post("/assets/images", response_model=AssetPublic, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile,
    product_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator")),
    settings: Settings = Depends(get_settings),
) -> AssetPublic:
    content = await file.read()
    try:
        suffix = validate_image_upload(file.filename or "image", file.content_type or "", content)
    except ValueError as exc:
        code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE if len(content) > 10 * 1024 * 1024 else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    if product_id and db.get(ProductRow, product_id) is None:
        raise HTTPException(status_code=404, detail="产品不存在")
    storage_key = f"{uuid4().hex}{suffix}"
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    (settings.upload_dir / storage_key).write_bytes(content)
    asset = Asset(
        owner_id=current_user.id,
        product_id=product_id,
        storage_key=storage_key,
        original_name=file.filename or storage_key,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset_public(asset)


@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "operator")),
    settings: Settings = Depends(get_settings),
) -> None:
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="素材不存在")
    remove_storage_file(settings.upload_dir, asset.storage_key)
    db.delete(asset)
    db.commit()
