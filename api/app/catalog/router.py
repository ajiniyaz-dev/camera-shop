"""Admin catalog management. Reads use require_admin. Writes use require_admin_write.

Manual edits set the matching lock. Source snapshot columns are not written here.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.auth.csrf import client_address
from app.auth.dependencies import get_db, get_settings_from_request, require_admin, require_admin_write
from app.config import Settings
from app.importing.images import object_key, sniff_image
from app.importing.normalize import normalize_model
from app.importing.slug import allocate_slug, product_slug, slug_part
from app.models import (
    AdminAuditLog,
    AdminUser,
    Brand,
    BrandTranslation,
    BusinessProfile,
    Category,
    CategoryTranslation,
    ImportFile,
    ImportJob,
    ImportRow,
    Product,
    ProductImage,
    ProductSourceRecord,
    ProductSpecification,
    ProductSpecificationTranslation,
    ProductTranslation,
)

router = APIRouter(prefix="/api/admin", tags=["catalog"])
_LOCALES = ("ru", "uz", "en")
_PAGE_MAX = 100
_IMAGE_MAX_BYTES = 8 * 1024 * 1024
_MIME_EXT = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}


class TranslationInput(BaseModel):
    localized_name: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=20000)


class SpecificationInput(BaseModel):
    sort_order: int = Field(ge=0, le=10000)
    name_ru: str = Field(min_length=1, max_length=300)
    value_ru: str = Field(min_length=1, max_length=2000)
    name_uz: str | None = Field(default=None, max_length=300)
    value_uz: str | None = Field(default=None, max_length=2000)
    name_en: str | None = Field(default=None, max_length=300)
    value_en: str | None = Field(default=None, max_length=2000)


class PriceInput(BaseModel):
    status: Literal["numeric", "on_request", "hidden"]
    amount: str | None = Field(default=None, max_length=20)


class ProductWrite(BaseModel):
    model_display: str = Field(min_length=1, max_length=300)
    option_label: str | None = Field(default=None, max_length=300)
    brand_id: int | None = None
    category_id: int | None = None
    product_kind: Literal["product", "service"] = "product"
    stock_status: Literal["in_stock", "out_of_stock"] = "in_stock"
    catalog_status: Literal["draft", "published", "archived"] = "draft"
    price: PriceInput = Field(default_factory=lambda: PriceInput(status="on_request"))
    translations: dict[str, TranslationInput] = Field(default_factory=dict)
    specifications: list[SpecificationInput] | None = None


class ArchiveBody(BaseModel):
    confirm: bool


class BrandWrite(BaseModel):
    name_ru: str = Field(min_length=1, max_length=200)
    name_uz: str | None = Field(default=None, max_length=200)
    name_en: str | None = Field(default=None, max_length=200)
    description_ru: str | None = Field(default=None, max_length=5000)
    is_published: bool = True


class CategoryWrite(BaseModel):
    name_ru: str = Field(min_length=1, max_length=200)
    name_uz: str | None = Field(default=None, max_length=200)
    name_en: str | None = Field(default=None, max_length=200)
    parent_id: int | None = None
    is_published: bool = True


class ImagePatch(BaseModel):
    is_primary: bool | None = None
    alt_text: str | None = Field(default=None, max_length=300)


class SocialLink(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    url: str = Field(min_length=1, max_length=500)


class ProfileWrite(BaseModel):
    public_name: str = Field(min_length=1, max_length=200)
    legal_name: str | None = Field(default=None, max_length=300)
    domain: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=80)
    email: str | None = Field(default=None, max_length=200)
    address: str | None = Field(default=None, max_length=500)
    opening_hours: str | None = Field(default=None, max_length=500)
    social_links: list[SocialLink] = Field(default_factory=list, max_length=8)


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


@router.get("/dashboard")
def dashboard(
    response: Response,
    _: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _no_store(response)
    status_rows = db.execute(
        select(Product.catalog_status, func.count()).group_by(Product.catalog_status)
    ).all()
    by_status = {status: count for status, count in status_rows}
    pending = db.scalar(
        select(func.count())
        .select_from(ImportRow)
        .join(ImportFile, ImportRow.import_file_id == ImportFile.id)
        .join(ImportJob, ImportFile.job_id == ImportJob.id)
        .where(
            ImportJob.status == "preview",
            ImportRow.action.in_(("possible_match", "conflict")),
            ImportRow.resolution == "pending",
        )
    ) or 0
    invalid_files = db.scalar(
        select(func.count())
        .select_from(ImportFile)
        .join(ImportJob, ImportFile.job_id == ImportJob.id)
        .where(ImportJob.status == "preview", ImportFile.validation_status == "invalid")
    ) or 0
    jobs = db.scalars(select(ImportJob).order_by(ImportJob.id.desc()).limit(8)).all()
    return {
        "products": {
            "total": sum(by_status.values()),
            "published": by_status.get("published", 0),
            "draft": by_status.get("draft", 0),
            "archived": by_status.get("archived", 0),
        },
        "brands": db.scalar(select(func.count()).select_from(Brand)) or 0,
        "categories": db.scalar(select(func.count()).select_from(Category)) or 0,
        "review": {"pending_conflicts": pending, "invalid_files": invalid_files},
        "recent_imports": [_job_brief(job) for job in jobs],
    }


@router.get("/products")
def list_products(
    response: Response,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=_PAGE_MAX),
    q: str | None = Query(default=None, max_length=200),
    catalog_status: str | None = Query(default=None),
    stock_status: str | None = Query(default=None),
    brand_id: int | None = Query(default=None),
    category_id: int | None = Query(default=None),
    sort: Literal["model", "updated", "price"] = "model",
    _: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _no_store(response)
    filters = []
    if catalog_status in {"draft", "published", "archived"}:
        filters.append(Product.catalog_status == catalog_status)
    if stock_status in {"in_stock", "out_of_stock"}:
        filters.append(Product.stock_status == stock_status)
    if brand_id is not None:
        filters.append(Product.brand_id == brand_id)
    if category_id is not None:
        filters.append(Product.category_id == category_id)
    if q and q.strip():
        term = f"%{q.strip().replace('%', '').replace('_', '')}%"
        filters.append(
            or_(
                Product.model_display.ilike(term),
                Product.option_label.ilike(term),
                Product.id.in_(
                    select(ProductTranslation.product_id).where(ProductTranslation.description.ilike(term))
                ),
            )
        )
    total = db.scalar(select(func.count()).select_from(Product).where(*filters)) or 0
    order = {
        "model": Product.model_display.asc(),
        "updated": Product.updated_at.desc(),
        "price": Product.public_price_amount.asc().nulls_last(),
    }[sort]
    rows = db.scalars(
        select(Product)
        .where(*filters)
        .options(selectinload(Product.brand).selectinload(Brand.translations))
        .order_by(order, Product.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "products": [_product_brief(product) for product in rows],
    }


@router.get("/products/{product_id}")
def read_product(
    product_id: int,
    response: Response,
    _: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _no_store(response)
    return _product_detail(_product_or_404(db, product_id))


@router.post("/products", status_code=201)
def create_product(
    body: ProductWrite,
    request: Request,
    response: Response,
    admin: AdminUser = Depends(require_admin_write),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> dict[str, object]:
    _no_store(response)
    _require_refs(db, body.brand_id, body.category_id)
    now = datetime.now(timezone.utc)
    status, amount, currency = _price_columns(body.price)
    taken = set(db.scalars(select(Product.slug)).all())
    brand_name = _brand_name(db, body.brand_id)
    product = Product(
        brand_id=body.brand_id,
        category_id=body.category_id,
        product_kind=body.product_kind,
        model_raw=body.model_display.strip(),
        model_display=body.model_display.strip(),
        model_normalized=normalize_model(body.model_display),
        option_label=_blank_none(body.option_label),
        public_price_status=status,
        public_price_amount=amount,
        public_currency=currency,
        stock_status=body.stock_status,
        slug=product_slug(brand_name, body.model_display.strip(), _blank_none(body.option_label), 0, taken),
        catalog_status=body.catalog_status,
        price_updated_at=now,
        model_locked=True,
        option_locked=body.option_label is not None,
        brand_locked=body.brand_id is not None,
        category_locked=body.category_id is not None,
        price_locked=True,
    )
    db.add(product)
    db.flush()
    _replace_translations(db, product, body.translations, locking=True)
    if body.specifications is not None:
        _replace_specifications(db, product, body.specifications)
    _audit(db, request, settings, admin, "product_created", "product", product.id, {"catalog_status": product.catalog_status})
    _commit(db)
    db.refresh(product)
    return _product_detail(_product_or_404(db, product.id))


@router.patch("/products/{product_id}")
def update_product(
    product_id: int,
    body: ProductWrite,
    request: Request,
    response: Response,
    admin: AdminUser = Depends(require_admin_write),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> dict[str, object]:
    _no_store(response)
    product = _product_or_404(db, product_id)
    _require_refs(db, body.brand_id, body.category_id)
    changes: list[str] = []
    now = datetime.now(timezone.utc)
    display = body.model_display.strip()
    if display != product.model_display:
        product.model_display = display
        product.model_raw = display
        product.model_normalized = normalize_model(display)
        product.model_locked = True
        changes.append("model_display")
    option = _blank_none(body.option_label)
    if option != product.option_label:
        product.option_label = option
        product.option_locked = True
        changes.append("option_label")
    if body.brand_id != product.brand_id:
        product.brand_id = body.brand_id
        product.brand_locked = True
        changes.append("brand")
    if body.category_id != product.category_id:
        product.category_id = body.category_id
        product.category_locked = True
        changes.append("category")
    if body.product_kind != product.product_kind:
        product.product_kind = body.product_kind
        changes.append("product_kind")
    if body.stock_status != product.stock_status:
        product.stock_status = body.stock_status
        changes.append("stock_status")
    if body.catalog_status != product.catalog_status:
        product.catalog_status = body.catalog_status
        changes.append("catalog_status")
    status, amount, currency = _price_columns(body.price)
    if (
        status != product.public_price_status
        or amount != product.public_price_amount
        or currency != product.public_currency
    ):
        product.public_price_status = status
        product.public_price_amount = amount
        product.public_currency = currency
        product.price_locked = True
        product.price_updated_at = now
        changes.append("price")
    if _replace_translations(db, product, body.translations, locking=True):
        changes.append("translations")
    if body.specifications is not None and _replace_specifications(db, product, body.specifications):
        changes.append("specifications")
    action = "product_price_changed" if "price" in changes else "product_updated"
    if body.catalog_status == "archived" and "catalog_status" in changes:
        action = "product_archived"
    _audit(db, request, settings, admin, action, "product", product.id, {"changes": changes})
    _commit(db)
    return _product_detail(_product_or_404(db, product.id))


@router.post("/products/{product_id}/archive")
def archive_product(
    product_id: int,
    body: ArchiveBody,
    request: Request,
    response: Response,
    admin: AdminUser = Depends(require_admin_write),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> dict[str, object]:
    _no_store(response)
    if not body.confirm:
        raise HTTPException(status_code=422, detail="Confirm before archiving this product.")
    product = _product_or_404(db, product_id)
    product.catalog_status = "archived"
    _audit(db, request, settings, admin, "product_archived", "product", product.id, {"catalog_status": "archived"})
    _commit(db)
    return _product_detail(product)


@router.post("/products/{product_id}/images", status_code=201)
def add_image(
    product_id: int,
    request: Request,
    response: Response,
    file: UploadFile = File(),
    alt_text: str | None = Form(default=None),
    admin: AdminUser = Depends(require_admin_write),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> dict[str, object]:
    _no_store(response)
    product = _product_or_404(db, product_id)
    content = _read_limited(file, _IMAGE_MAX_BYTES)
    stored = _store_image(Path(settings.media_root), content)
    existing = {image.sha256.strip() for image in product.images}
    if stored["sha256"] in existing:
        raise HTTPException(status_code=409, detail="This image is already attached to the product.")
    has_primary = any(image.is_primary and image.association_status != "rejected" for image in product.images)
    sort_order = max((image.sort_order for image in product.images), default=-1) + 1
    image = ProductImage(
        product_id=product.id,
        storage_backend="local",
        object_key=stored["object_key"],
        mime_type=stored["mime_type"],
        byte_size=len(content),
        sha256=stored["sha256"],
        sort_order=sort_order,
        is_primary=not has_primary,
        alt_text=_blank_none(alt_text),
        association_status="confirmed",
    )
    db.add(image)
    db.flush()
    _audit(db, request, settings, admin, "image_added", "product", product.id, {"image_id": image.id})
    _commit(db)
    return _image_public(image)


@router.patch("/products/{product_id}/images/{image_id}")
def update_image(
    product_id: int,
    image_id: int,
    body: ImagePatch,
    request: Request,
    response: Response,
    admin: AdminUser = Depends(require_admin_write),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> dict[str, object]:
    _no_store(response)
    product = _product_or_404(db, product_id)
    image = _image_or_404(product, image_id)
    if body.alt_text is not None:
        image.alt_text = _blank_none(body.alt_text)
    if body.is_primary:
        for other in product.images:
            if other.id != image.id:
                other.is_primary = False
        db.flush()
        image.is_primary = True
        image.association_status = "confirmed"
    _audit(db, request, settings, admin, "image_updated", "product", product.id, {"image_id": image.id})
    _commit(db)
    return _image_public(image)


@router.delete("/products/{product_id}/images/{image_id}", status_code=204)
def delete_image(
    product_id: int,
    image_id: int,
    request: Request,
    response: Response,
    admin: AdminUser = Depends(require_admin_write),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> Response:
    _no_store(response)
    product = _product_or_404(db, product_id)
    image = _image_or_404(product, image_id)
    was_primary = image.is_primary
    db.delete(image)
    db.flush()
    if was_primary:
        remaining = [item for item in product.images if item.id != image.id and item.association_status != "rejected"]
        if remaining and not any(item.is_primary for item in remaining):
            remaining[0].is_primary = True
    _audit(db, request, settings, admin, "image_removed", "product", product.id, {"image_id": image_id})
    _commit(db)
    return Response(status_code=204)


@router.get("/brands")
def list_brands(
    response: Response,
    _: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _no_store(response)
    rows = db.scalars(select(Brand).options(selectinload(Brand.translations)).order_by(Brand.id)).all()
    return {"brands": [_brand_public(brand) for brand in rows]}


@router.post("/brands", status_code=201)
def create_brand(
    body: BrandWrite,
    request: Request,
    response: Response,
    admin: AdminUser = Depends(require_admin_write),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> dict[str, object]:
    _no_store(response)
    taken = set(db.scalars(select(Brand.slug)).all())
    brand = Brand(slug=allocate_slug(slug_part(body.name_ru), taken), is_published=body.is_published)
    db.add(brand)
    db.flush()
    _set_named_translations(db, BrandTranslation, "brand_id", brand.id, body)
    _audit(db, request, settings, admin, "brand_created", "brand", brand.id, {"slug": brand.slug})
    _commit(db)
    db.refresh(brand)
    return _brand_public(brand)


@router.patch("/brands/{brand_id}")
def update_brand(
    brand_id: int,
    body: BrandWrite,
    request: Request,
    response: Response,
    admin: AdminUser = Depends(require_admin_write),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> dict[str, object]:
    _no_store(response)
    brand = db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found.")
    brand.is_published = body.is_published
    _set_named_translations(db, BrandTranslation, "brand_id", brand.id, body)
    _audit(db, request, settings, admin, "brand_updated", "brand", brand.id, {})
    _commit(db)
    return _brand_public(brand)


@router.get("/categories")
def list_categories(
    response: Response,
    _: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _no_store(response)
    rows = db.scalars(select(Category).options(selectinload(Category.translations)).order_by(Category.id)).all()
    return {"categories": [_category_public(category) for category in rows]}


@router.post("/categories", status_code=201)
def create_category(
    body: CategoryWrite,
    request: Request,
    response: Response,
    admin: AdminUser = Depends(require_admin_write),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> dict[str, object]:
    _no_store(response)
    _require_parent(db, body.parent_id, None)
    sibling_slugs = _sibling_slugs(db, body.parent_id)
    category = Category(
        parent_id=body.parent_id,
        slug=allocate_slug(slug_part(body.name_ru), sibling_slugs),
        sort_order=0,
        is_published=body.is_published,
    )
    db.add(category)
    db.flush()
    _set_named_translations(db, CategoryTranslation, "category_id", category.id, body, description=False)
    _audit(db, request, settings, admin, "category_created", "category", category.id, {"slug": category.slug})
    _commit(db)
    return _category_public(category)


@router.patch("/categories/{category_id}")
def update_category(
    category_id: int,
    body: CategoryWrite,
    request: Request,
    response: Response,
    admin: AdminUser = Depends(require_admin_write),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> dict[str, object]:
    _no_store(response)
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found.")
    _require_parent(db, body.parent_id, category.id)
    category.parent_id = body.parent_id
    category.is_published = body.is_published
    _set_named_translations(db, CategoryTranslation, "category_id", category.id, body, description=False)
    _audit(db, request, settings, admin, "category_updated", "category", category.id, {})
    _commit(db)
    return _category_public(category)


@router.get("/profile")
def read_profile(
    response: Response,
    _: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _no_store(response)
    return _profile_public(_profile_or_404(db))


@router.patch("/profile")
def update_profile(
    body: ProfileWrite,
    request: Request,
    response: Response,
    admin: AdminUser = Depends(require_admin_write),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> dict[str, object]:
    _no_store(response)
    profile = _profile_or_404(db)
    for link in body.social_links:
        if not link.url.startswith(("https://", "http://")):
            raise HTTPException(status_code=422, detail="Social links must start with http:// or https://.")
    profile.public_name = body.public_name.strip()
    profile.legal_name = _blank_none(body.legal_name)
    profile.domain = _blank_none(body.domain)
    profile.phone = _blank_none(body.phone)
    profile.email = _blank_none(body.email)
    profile.address = _blank_none(body.address)
    profile.opening_hours = _blank_none(body.opening_hours)
    profile.social_links = [link.model_dump() for link in body.social_links]
    profile.updated_at = datetime.now(timezone.utc)
    _audit(db, request, settings, admin, "profile_updated", "business_profile", profile.id, {})
    _commit(db)
    return _profile_public(profile)


def _job_brief(job: ImportJob) -> dict[str, object]:
    summary = job.summary or {}
    return {
        "id": job.id,
        "status": job.status,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "replace_prices": job.replace_prices,
        "publish_new_products": job.publish_new_products,
        "error_message": job.error_message,
        "rejected_files": summary.get("rejected_files") or [],
        "result": summary.get("result"),
    }


def _product_or_404(db: Session, product_id: int) -> Product:
    product = db.scalar(
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.translations),
            selectinload(Product.images),
            selectinload(Product.specifications).selectinload(ProductSpecification.translations),
            selectinload(Product.brand).selectinload(Brand.translations),
            selectinload(Product.category).selectinload(Category.translations),
            selectinload(Product.source_record),
        )
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


def _product_brief(product: Product) -> dict[str, object]:
    return {
        "id": product.id,
        "model_display": product.model_display,
        "option_label": product.option_label,
        "slug": product.slug,
        "brand": _ru_name(product.brand.translations) if product.brand is not None else None,
        "catalog_status": product.catalog_status,
        "stock_status": product.stock_status,
        "public_price_status": product.public_price_status,
        "public_price_amount": _money(product.public_price_amount),
        "public_currency": product.public_currency,
        "price_locked": product.price_locked,
    }


def _product_detail(product: Product) -> dict[str, object]:
    source = product.source_record
    return {
        **_product_brief(product),
        "product_kind": product.product_kind,
        "brand_id": product.brand_id,
        "category_id": product.category_id,
        "model_locked": product.model_locked,
        "option_locked": product.option_locked,
        "brand_locked": product.brand_locked,
        "category_locked": product.category_locked,
        "translations": {
            item.locale: {
                "localized_name": item.localized_name,
                "description": item.description,
                "origin": item.origin,
                "description_locked": item.description_locked,
            }
            for item in product.translations
        },
        "specifications": [
            {
                "id": spec.id,
                "sort_order": spec.sort_order,
                "translations": {
                    item.locale: {"name": item.name, "value": item.value} for item in spec.translations
                },
            }
            for spec in sorted(product.specifications, key=lambda item: (item.sort_order, item.id))
        ],
        "images": [_image_public(image) for image in sorted(product.images, key=lambda item: item.sort_order)],
        "source": None
        if source is None
        else {
            "source_code": source.source_code,
            "source_worksheet": source.source_worksheet,
            "source_row": source.source_row,
            "source_price_kind": source.source_price_kind,
            "source_price_amount": _money(source.source_price_amount),
            "internal_note": source.internal_note,
            "absent_from_latest": source.absent_from_latest,
        },
    }


def _image_public(image: ProductImage) -> dict[str, object]:
    return {
        "id": image.id,
        "mime_type": image.mime_type,
        "sha256": image.sha256.strip(),
        "is_primary": image.is_primary,
        "sort_order": image.sort_order,
        "alt_text": image.alt_text,
        "association_status": image.association_status,
        "url": f"/media/{image.object_key}",
    }


def _brand_public(brand: Brand) -> dict[str, object]:
    names = {item.locale: item.name for item in brand.translations}
    description = next((item.description for item in brand.translations if item.locale == "ru"), None)
    return {
        "id": brand.id,
        "slug": brand.slug,
        "is_published": brand.is_published,
        "name_ru": names.get("ru"),
        "name_uz": names.get("uz"),
        "name_en": names.get("en"),
        "description_ru": description,
    }


def _category_public(category: Category) -> dict[str, object]:
    names = {item.locale: item.name for item in category.translations}
    return {
        "id": category.id,
        "slug": category.slug,
        "parent_id": category.parent_id,
        "is_published": category.is_published,
        "name_ru": names.get("ru"),
        "name_uz": names.get("uz"),
        "name_en": names.get("en"),
    }


def _profile_public(profile: BusinessProfile) -> dict[str, object]:
    return {
        "public_name": profile.public_name,
        "legal_name": profile.legal_name,
        "domain": profile.domain,
        "phone": profile.phone,
        "email": profile.email,
        "address": profile.address,
        "opening_hours": profile.opening_hours,
        "social_links": profile.social_links or [],
    }


def _profile_or_404(db: Session) -> BusinessProfile:
    profile = db.get(BusinessProfile, 1)
    if profile is None:
        raise HTTPException(status_code=404, detail="Company profile not found.")
    return profile


def _require_refs(db: Session, brand_id: int | None, category_id: int | None) -> None:
    if brand_id is not None and db.get(Brand, brand_id) is None:
        raise HTTPException(status_code=422, detail="Brand not found.")
    if category_id is not None and db.get(Category, category_id) is None:
        raise HTTPException(status_code=422, detail="Category not found.")


def _require_parent(db: Session, parent_id: int | None, category_id: int | None) -> None:
    if parent_id is None:
        return
    if parent_id == category_id:
        raise HTTPException(status_code=422, detail="A category cannot be its own parent.")
    seen: set[int] = set()
    current = parent_id
    while current is not None:
        if current in seen or current == category_id:
            raise HTTPException(status_code=422, detail="Category parents cannot form a cycle.")
        seen.add(current)
        parent = db.get(Category, current)
        if parent is None:
            raise HTTPException(status_code=422, detail="Parent category not found.")
        current = parent.parent_id


def _sibling_slugs(db: Session, parent_id: int | None) -> set[str]:
    query = select(Category.slug)
    if parent_id is None:
        query = query.where(Category.parent_id.is_(None))
    else:
        query = query.where(Category.parent_id == parent_id)
    return set(db.scalars(query).all())


def _price_columns(price: PriceInput) -> tuple[str, Decimal | None, str | None]:
    amount = _parse_amount(price.amount)
    if price.status == "numeric":
        if amount is None:
            raise HTTPException(status_code=422, detail="A numeric price needs an amount.")
        return "numeric", amount, "USD"
    if price.status == "on_request":
        if amount is not None:
            raise HTTPException(status_code=422, detail="An on-request price cannot also have an amount.")
        return "on_request", None, None
    return "hidden", amount, None


def _parse_amount(value: str | None) -> Decimal | None:
    if value is None or not value.strip():
        return None
    try:
        amount = Decimal(value.strip())
    except InvalidOperation as exc:
        raise HTTPException(status_code=422, detail="Enter the price as a USD decimal.") from exc
    if amount < 0 or amount != amount.quantize(Decimal("0.01")):
        raise HTTPException(status_code=422, detail="Prices use two decimal places and cannot be negative.")
    return amount.quantize(Decimal("0.01"))


def _replace_translations(
    db: Session,
    product: Product,
    translations: dict[str, TranslationInput],
    *,
    locking: bool,
) -> bool:
    changed = False
    current = {item.locale: item for item in product.translations}
    for locale in _LOCALES:
        incoming = translations.get(locale)
        name = _blank_none(incoming.localized_name) if incoming else None
        description = _blank_none(incoming.description) if incoming else None
        existing = current.get(locale)
        if locale != "ru" and name is None and description is None:
            if existing is not None:
                db.delete(existing)
                changed = True
            continue
        if existing is None:
            db.add(
                ProductTranslation(
                    product_id=product.id,
                    locale=locale,
                    localized_name=name,
                    description=description,
                    origin="manual" if description else "empty",
                    description_locked=bool(description) and locking,
                )
            )
            changed = True
            continue
        if existing.localized_name != name or existing.description != description:
            if existing.description != description and locking:
                existing.description_locked = True
                existing.origin = "manual" if description else "empty"
            existing.localized_name = name
            existing.description = description
            changed = True
    return changed


def _replace_specifications(db: Session, product: Product, specs: list[SpecificationInput]) -> bool:
    for existing in list(product.specifications):
        db.delete(existing)
    db.flush()
    for spec in specs:
        row = ProductSpecification(product_id=product.id, sort_order=spec.sort_order)
        db.add(row)
        db.flush()
        db.add(ProductSpecificationTranslation(specification_id=row.id, locale="ru", name=spec.name_ru.strip(), value=spec.value_ru.strip()))
        if spec.name_uz and spec.value_uz:
            db.add(
                ProductSpecificationTranslation(
                    specification_id=row.id, locale="uz", name=spec.name_uz.strip(), value=spec.value_uz.strip()
                )
            )
        if spec.name_en and spec.value_en:
            db.add(
                ProductSpecificationTranslation(
                    specification_id=row.id, locale="en", name=spec.name_en.strip(), value=spec.value_en.strip()
                )
            )
    return True


def _set_named_translations(
    db: Session,
    model: type[BrandTranslation] | type[CategoryTranslation],
    fk_name: str,
    entity_id: int,
    body: BrandWrite | CategoryWrite,
    *,
    description: bool = True,
) -> None:
    names = {"ru": body.name_ru.strip(), "uz": _blank_none(body.name_uz), "en": _blank_none(body.name_en)}
    for locale, name in names.items():
        if name is None:
            if locale != "ru":
                existing = db.get(model, {fk_name: entity_id, "locale": locale})
                if existing is not None:
                    db.delete(existing)
            continue
        values: dict[str, Any] = {fk_name: entity_id, "locale": locale, "name": name}
        if description and locale == "ru" and isinstance(body, BrandWrite):
            values["description"] = _blank_none(body.description_ru)
        existing = db.get(model, {fk_name: entity_id, "locale": locale})
        if existing is None:
            db.add(model(**values))
        else:
            existing.name = name
            if description and locale == "ru" and isinstance(body, BrandWrite):
                existing.description = _blank_none(body.description_ru)


def _brand_name(db: Session, brand_id: int | None) -> str | None:
    if brand_id is None:
        return None
    brand = db.scalar(select(Brand).where(Brand.id == brand_id).options(selectinload(Brand.translations)))
    if brand is None:
        return None
    return _ru_name(brand.translations)


def _ru_name(translations: list[Any]) -> str | None:
    for item in translations:
        if item.locale == "ru":
            return item.name
    return None


def _image_or_404(product: Product, image_id: int) -> ProductImage:
    for image in product.images:
        if image.id == image_id:
            return image
    raise HTTPException(status_code=404, detail="Image not found.")


def _read_limited(upload: UploadFile, limit: int) -> bytes:
    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = upload.file.read(1024 * 1024)
        if not chunk:
            break
        size += len(chunk)
        if size > limit:
            raise HTTPException(status_code=413, detail="The image is larger than 8 MB.")
        chunks.append(chunk)
    if size == 0:
        raise HTTPException(status_code=422, detail="Choose an image file.")
    return b"".join(chunks)


def _store_image(root: Path, content: bytes) -> dict[str, str]:
    mime = sniff_image(content)
    if mime is None:
        raise HTTPException(status_code=422, detail="Only PNG, JPEG, and WebP images can be stored.")
    digest = hashlib.sha256(content).hexdigest()
    key = object_key(digest, _MIME_EXT[mime])
    path = _media_path(root, key)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_name(path.name + ".partial")
        partial.write_bytes(content)
        partial.replace(path)
    return {"object_key": key, "mime_type": mime, "sha256": digest}


def _media_path(root: Path, key: str) -> Path:
    base = root.resolve()
    path = (base / key).resolve()
    if base not in path.parents:
        raise HTTPException(status_code=422, detail="The image could not be stored.")
    return path


def _blank_none(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _money(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return f"{value.quantize(Decimal('0.01'))}"


def _audit(
    db: Session,
    request: Request,
    settings: Settings,
    admin: AdminUser,
    action: str,
    entity_type: str,
    entity_id: int,
    detail: dict[str, object],
) -> None:
    db.add(
        AdminAuditLog(
            actor_id=admin.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            detail=detail,
            ip_address=client_address(request, settings),
        )
    )


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="That value is already in use.") from exc
