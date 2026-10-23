"""Published catalog reads. Responses use public fields only."""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import get_db
from app.models import (
    Brand,
    Category,
    Product,
    ProductImage,
    ProductSourceRecord,
    ProductSpecification,
    ProductTranslation,
)
from app.models.profile import BusinessProfile
from app.pricing import EZVIZ_FACTOR, HIKVISION_FACTOR, public_display_price

LOCALES = ("ru", "uz", "en")
PUBLIC_IMAGES = {"high", "confirmed"}
MAX_PAGE_SIZE = 48
_CYRILLIC = re.compile(r"[А-Яа-яЁё]")
router = APIRouter(prefix="/api/public", tags=["public"])


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


router.dependencies.append(Depends(_no_store))


def _locale(value: str) -> str:
    if value not in LOCALES:
        raise HTTPException(status_code=422, detail="The locale is not supported.")
    return value


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _like(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _text(rows: list, locale: str, attr: str) -> tuple[str | None, bool]:
    by_locale = {row.locale: row for row in rows}
    selected = _clean(getattr(by_locale.get(locale), attr, None))
    if selected:
        return selected, False
    if locale == "ru":
        return None, False
    original = _clean(getattr(by_locale.get("ru"), attr, None))
    if original:
        return original, True
    return None, False


def _own(rows: list, locale: str, attr: str) -> str | None:
    """Locale value only. SEO titles do not fall back to Russian."""
    by_locale = {row.locale: row for row in rows}
    return _clean(getattr(by_locale.get(locale), attr, None))


def _stamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _published_filter():
    return and_(Product.catalog_status == "published", Product.deleted_at.is_(None))


def _brands_without_published_products(db: Session, brands: list[Brand]) -> set[int]:
    brand_ids = [brand.id for brand in brands]
    if not brand_ids:
        return set()
    populated = set(
        db.scalars(
            select(Product.brand_id).where(Product.brand_id.in_(brand_ids), _published_filter())
        ).all()
    )
    return {brand_id for brand_id in brand_ids if brand_id not in populated}


def _navigable_brands(db: Session) -> list[Brand]:
    brands = list(
        db.scalars(
            select(Brand)
            .where(Brand.is_published.is_(True))
            .options(selectinload(Brand.translations))
            .order_by(Brand.slug, Brand.id)
        ).all()
    )
    hidden = _brands_without_published_products(db, brands)
    return [brand for brand in brands if brand.id not in hidden]


def _product_options():
    return (
        selectinload(Product.translations),
        selectinload(Product.images),
        selectinload(Product.brand).selectinload(Brand.translations),
        selectinload(Product.category).selectinload(Category.translations),
        selectinload(Product.specifications).selectinload(ProductSpecification.translations),
        selectinload(Product.source_record),
    )


def _categories(db: Session) -> dict[int, Category]:
    rows = db.scalars(select(Category).options(selectinload(Category.translations))).all()
    return {row.id: row for row in rows}


def _descendant_ids(index: dict[int, Category], root_id: int) -> set[int]:
    children: dict[int | None, list[int]] = {}
    for category in index.values():
        if not category.is_published:
            continue
        children.setdefault(category.parent_id, []).append(category.id)
    found = {root_id}
    pending = [root_id]
    while pending:
        current = pending.pop()
        for child_id in children.get(current, []):
            if child_id not in found:
                found.add(child_id)
                pending.append(child_id)
    return found


def _category_path(index: dict[int, Category], category: Category) -> list[Category]:
    path: list[Category] = []
    current: Category | None = category
    seen: set[int] = set()
    while current is not None and current.id not in seen:
        seen.add(current.id)
        path.append(current)
        parent_id = current.parent_id
        current = index.get(parent_id) if parent_id is not None else None
    path.reverse()
    return path


def _find_category(index: dict[int, Category], slug: str, parent_slug: str | None) -> Category:
    matches = [
        category
        for category in index.values()
        if category.is_published and category.slug == slug
    ]
    if parent_slug is None:
        matches = [category for category in matches if category.parent_id is None]
    else:
        matches = [
            category
            for category in matches
            if category.parent_id is not None
            and index.get(category.parent_id) is not None
            and index[category.parent_id].is_published
            and index[category.parent_id].slug == parent_slug
        ]
    if len(matches) != 1:
        raise HTTPException(status_code=404, detail="Category not found.")
    return matches[0]


def _brand(brand: Brand | None, locale: str) -> dict[str, object] | None:
    if brand is None or not brand.is_published:
        return None
    name, fallback = _text(brand.translations, locale, "name")
    description, description_fallback = _text(brand.translations, locale, "description")
    return {
        "slug": brand.slug,
        "name": name or brand.slug,
        "description": description,
        "translation_fallback": fallback or description_fallback,
        "description_fallback": description_fallback,
    }


def _category_public(index: dict[int, Category], category: Category | None, locale: str) -> dict[str, object] | None:
    if category is None or not category.is_published:
        return None
    name, fallback = _text(category.translations, locale, "name")
    description, description_fallback = _text(category.translations, locale, "description")
    path = [item for item in _category_path(index, category) if item.is_published]
    parent = path[-2] if len(path) > 1 else None
    return {
        "slug": category.slug,
        "parent_slug": parent.slug if parent is not None else None,
        "name": name or category.slug,
        "description": description,
        "translation_fallback": fallback or description_fallback,
        "description_fallback": description_fallback,
        "breadcrumb": [
            {
                "slug": item.slug,
                "parent_slug": path[position - 1].slug if position else None,
                "name": _text(item.translations, locale, "name")[0] or item.slug,
            }
            for position, item in enumerate(path)
        ],
    }


def _price(product: Product) -> dict[str, object]:
    source = product.source_record
    return public_display_price(
        public_price_status=product.public_price_status,
        public_price_amount=product.public_price_amount,
        source_code=source.source_code if source is not None else None,
    )


def _displayed_amount_column():
    """SQL expression for the public soʻm amount. Matches public_display_price."""
    return case(
        (
            and_(
                Product.public_price_status == "numeric",
                ProductSourceRecord.source_code == "hikvision",
                Product.public_price_amount.is_not(None),
            ),
            Product.public_price_amount * HIKVISION_FACTOR,
        ),
        (
            and_(
                Product.public_price_status == "numeric",
                ProductSourceRecord.source_code == "ezviz",
                Product.public_price_amount.is_not(None),
            ),
            Product.public_price_amount * EZVIZ_FACTOR,
        ),
        else_=None,
    )


def _image_alt(stored: str | None, locale_name: str) -> str:
    """Prefer a non-Cyrillic locale name over a Cyrillic stored alt (import/model text)."""
    cleaned_stored = _clean(stored)
    cleaned_name = _clean(locale_name) or ""
    if not cleaned_stored:
        return cleaned_name
    if (
        cleaned_name
        and _CYRILLIC.search(cleaned_stored) is not None
        and _CYRILLIC.search(cleaned_name) is None
    ):
        return cleaned_name
    return cleaned_stored


def _image(image: ProductImage, alt: str) -> dict[str, object]:
    return {
        "url": f"/media/{image.object_key}",
        "alt": _image_alt(image.alt_text, alt),
        "width": image.width,
        "height": image.height,
        "is_primary": image.is_primary,
    }


def _visible_images(product: Product) -> list[ProductImage]:
    visible = [image for image in product.images if image.association_status in PUBLIC_IMAGES]
    return sorted(visible, key=lambda image: (not image.is_primary, image.sort_order, image.id))


def _has_public_image():
    """True when a product would show a catalog photo (high/confirmed association)."""
    return exists(
        select(ProductImage.id).where(
            ProductImage.product_id == Product.id,
            ProductImage.association_status.in_(PUBLIC_IMAGES),
        )
    )


def _card(product: Product, locale: str, index: dict[int, Category]) -> dict[str, object]:
    name, name_fallback = _text(product.translations, locale, "localized_name")
    if not name:
        name = product.model_display
        name_fallback = False
    elif name_fallback and _CYRILLIC.search(name) is None:
        name_fallback = False
    images = _visible_images(product)
    return {
        "slug": product.slug,
        "product_kind": product.product_kind,
        "model_display": product.model_display,
        "option_label": _clean(product.option_label),
        "name": name,
        "translation_fallback": name_fallback,
        "brand": _brand(product.brand, locale),
        "category": _category_public(index, product.category, locale),
        "price": _price(product),
        "out_of_stock": product.stock_status == "out_of_stock",
        "image": _image(images[0], name) if images else None,
    }


def _detail(product: Product, locale: str, index: dict[int, Category]) -> dict[str, object]:
    card = _card(product, locale, index)
    description, description_fallback = _text(product.translations, locale, "description")
    specifications = []
    for spec in sorted(product.specifications, key=lambda item: (item.sort_order, item.id)):
        spec_name, name_fallback = _text(spec.translations, locale, "name")
        spec_value, value_fallback = _text(spec.translations, locale, "value")
        if not spec_name or not spec_value:
            continue
        specifications.append(
            {
                "name": spec_name,
                "value": spec_value,
                "translation_fallback": name_fallback or value_fallback,
            }
        )
    images = _visible_images(product)
    card.update(
        {
            "description": description,
            "description_fallback": description_fallback,
            "seo_title": _own(product.translations, locale, "seo_title"),
            "seo_description": _own(product.translations, locale, "seo_description"),
            "specifications": specifications,
            "images": [_image(image, str(card["name"])) for image in images],
        }
    )
    return card


def _bounds(min_price: str | None, max_price: str | None) -> tuple[Decimal | None, Decimal | None]:
    low = _decimal_bound(min_price, "min_price")
    high = _decimal_bound(max_price, "max_price")
    if low is not None and high is not None and low > high:
        raise HTTPException(status_code=422, detail="The price range is invalid.")
    return low, high


def _decimal_bound(value: str | None, field: str) -> Decimal | None:
    if value is None or not value.strip():
        return None
    try:
        amount = Decimal(value.strip())
    except InvalidOperation as exc:
        raise HTTPException(status_code=422, detail=f"{field} is invalid.") from exc
    if amount < 0 or amount != amount.quantize(Decimal("1")):
        raise HTTPException(status_code=422, detail=f"{field} is invalid.")
    return amount


def _company(db: Session) -> dict[str, object]:
    profile = db.get(BusinessProfile, 1)
    if profile is None:
        return {"name": "HikVision"}
    body: dict[str, object] = {"name": profile.public_name}
    for field in ("phone", "email", "address", "opening_hours"):
        value = _clean(getattr(profile, field))
        if value:
            body[field] = value
    logo = _clean(profile.logo_object_key)
    if logo and logo.startswith("objects/") and ".." not in logo:
        body["logo_url"] = f"/media/{logo}"
    links = []
    for item in profile.social_links or []:
        if not isinstance(item, dict):
            continue
        label = _clean(str(item.get("label") or ""))
        url = _clean(str(item.get("url") or ""))
        if label and url and url.startswith(("http://", "https://")):
            links.append({"label": label, "url": url})
    if links:
        body["social_links"] = links
    return body


def _category_node(category: Category, locale: str, counts: dict[int, int], children: list[dict[str, object]]) -> dict[str, object]:
    name, fallback = _text(category.translations, locale, "name")
    description, description_fallback = _text(category.translations, locale, "description")
    return {
        "slug": category.slug,
        "name": name or category.slug,
        "description": description,
        "translation_fallback": fallback or description_fallback,
        "product_count": counts.get(category.id, 0),
        "children": children,
    }


def _counts(db: Session, index: dict[int, Category]) -> dict[int, int]:
    rows = db.execute(
        select(Product.category_id, func.count())
        .where(_published_filter(), Product.category_id.is_not(None))
        .group_by(Product.category_id)
    ).all()
    direct = {int(category_id): int(total) for category_id, total in rows if category_id is not None}
    totals: dict[int, int] = {}
    for category in index.values():
        if not category.is_published:
            continue
        totals[category.id] = sum(direct.get(item, 0) for item in _descendant_ids(index, category.id))
    return totals


def _build_tree(index: dict[int, Category], locale: str, counts: dict[int, int]) -> list[dict[str, object]]:
    children: dict[int | None, list[Category]] = {}
    for category in index.values():
        if category.is_published:
            children.setdefault(category.parent_id, []).append(category)

    def build(category: Category) -> dict[str, object]:
        nested = [
            build(child)
            for child in sorted(children.get(category.id, []), key=lambda item: (item.sort_order, item.id))
        ]
        return _category_node(category, locale, counts, nested)

    roots = children.get(None, [])
    return [build(category) for category in sorted(roots, key=lambda item: (item.sort_order, item.id))]


@router.get("/home")
def home(locale: str = Query(), db: Session = Depends(get_db)) -> dict[str, object]:
    selected = _locale(locale)
    index = _categories(db)
    counts = _counts(db, index)
    products = db.scalars(
        select(Product)
        .where(_published_filter())
        .options(*_product_options())
        .order_by(Product.updated_at.desc(), Product.id.desc())
        .limit(8)
    ).all()
    return {
        "locale": selected,
        "company": _company(db),
        "categories": _build_tree(index, selected, counts),
        "products": [_card(product, selected, index) for product in products],
    }


@router.get("/company")
def company(locale: str = Query(), db: Session = Depends(get_db)) -> dict[str, object]:
    _locale(locale)
    return _company(db)


@router.get("/categories")
def categories(locale: str = Query(), db: Session = Depends(get_db)) -> dict[str, object]:
    selected = _locale(locale)
    index = _categories(db)
    return {"locale": selected, "categories": _build_tree(index, selected, _counts(db, index))}


@router.get("/categories/{parent_slug}/{slug}")
def nested_category(
    parent_slug: str,
    slug: str,
    locale: str = Query(),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return _category_detail(db, _locale(locale), slug, parent_slug)


@router.get("/categories/{slug}")
def category_detail(slug: str, locale: str = Query(), db: Session = Depends(get_db)) -> dict[str, object]:
    return _category_detail(db, _locale(locale), slug, None)


def _category_detail(db: Session, locale: str, slug: str, parent_slug: str | None) -> dict[str, object]:
    index = _categories(db)
    category = _find_category(index, slug, parent_slug)
    counts = _counts(db, index)
    public = _category_public(index, category, locale) or {}
    child_rows = sorted(
        (
            child
            for child in index.values()
            if child.is_published and child.parent_id == category.id
        ),
        key=lambda item: (item.sort_order, item.id),
    )
    public["seo_title"] = _own(category.translations, locale, "seo_title")
    public["seo_description"] = _own(category.translations, locale, "seo_description")
    public["product_count"] = counts.get(category.id, 0)
    public["children"] = [
        {
            "slug": child.slug,
            "parent_slug": category.slug,
            "name": _text(child.translations, locale, "name")[0] or child.slug,
            "product_count": counts.get(child.id, 0),
        }
        for child in child_rows
    ]
    return public


@router.get("/brands/{slug}")
def brand_detail(slug: str, locale: str = Query(), db: Session = Depends(get_db)) -> dict[str, object]:
    selected = _locale(locale)
    brand = db.scalar(
        select(Brand).where(Brand.slug == slug, Brand.is_published.is_(True)).options(selectinload(Brand.translations))
    )
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found.")
    if brand.id in _brands_without_published_products(db, [brand]):
        raise HTTPException(status_code=404, detail="Brand not found.")
    public = _brand(brand, selected)
    if public is None:
        return {}
    public["seo_title"] = _own(brand.translations, selected, "seo_title")
    public["seo_description"] = _own(brand.translations, selected, "seo_description")
    return public


@router.get("/products")
def products(
    locale: str = Query(),
    q: str | None = Query(default=None, max_length=80),
    category: str | None = Query(default=None, max_length=120),
    parent: str | None = Query(default=None, max_length=120),
    brand: str | None = Query(default=None, max_length=120),
    min_price: str | None = Query(default=None, max_length=20),
    max_price: str | None = Query(default=None, max_length=20),
    sort: str = Query(default="model"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    selected = _locale(locale)
    if sort not in {"model", "name", "newest", "price_asc", "price_desc"}:
        raise HTTPException(status_code=422, detail="The sort is not supported.")
    low, high = _bounds(min_price, max_price)
    index = _categories(db)
    filters = [_published_filter()]
    query_text = _clean(q)
    if query_text:
        pattern = _like(query_text)
        filters.append(
            or_(
                Product.model_display.ilike(pattern, escape="\\"),
                Product.model_normalized.ilike(pattern, escape="\\"),
                Product.option_label.ilike(pattern, escape="\\"),
                Product.id.in_(
                    select(ProductTranslation.product_id).where(
                        or_(
                            ProductTranslation.localized_name.ilike(pattern, escape="\\"),
                            ProductTranslation.description.ilike(pattern, escape="\\"),
                        )
                    )
                ),
            )
        )
    if category:
        matched = _find_category(index, category, _clean(parent))
        filters.append(Product.category_id.in_(_descendant_ids(index, matched.id)))
    if brand:
        matched_brand = db.scalar(
            select(Brand)
            .where(Brand.slug == brand, Brand.is_published.is_(True))
            .options(selectinload(Brand.translations))
        )
        if matched_brand is None or matched_brand.id in _brands_without_published_products(db, [matched_brand]):
            raise HTTPException(status_code=404, detail="Brand not found.")
        filters.append(Product.brand_id == matched_brand.id)
    displayed = _displayed_amount_column()
    if low is not None or high is not None:
        filters.append(displayed.is_not(None))
        if low is not None:
            filters.append(displayed >= low)
        if high is not None:
            filters.append(displayed <= high)
    base = select(Product).outerjoin(ProductSourceRecord, ProductSourceRecord.product_id == Product.id)
    total = db.scalar(select(func.count()).select_from(Product).outerjoin(ProductSourceRecord, ProductSourceRecord.product_id == Product.id).where(*filters)) or 0
    name_sort = func.coalesce(
        select(ProductTranslation.localized_name)
        .where(ProductTranslation.product_id == Product.id, ProductTranslation.locale == selected)
        .correlate(Product)
        .scalar_subquery(),
        Product.model_display,
    )
    order = {
        "model": (Product.model_display.asc(), Product.id.asc()),
        "name": (name_sort.asc(), Product.id.asc()),
        "newest": (Product.updated_at.desc(), Product.id.desc()),
        "price_asc": (displayed.asc().nulls_last(), Product.id.asc()),
        "price_desc": (displayed.desc().nulls_last(), Product.id.asc()),
    }[sort]
    rows = db.scalars(
        base.where(*filters)
        .options(*_product_options())
        .order_by(case((_has_public_image(), 0), else_=1), *order)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    brands = _navigable_brands(db)
    return {
        "locale": selected,
        "page": page,
        "page_size": page_size,
        "total": total,
        "sort": sort,
        "products": [_card(product, selected, index) for product in rows],
        "brands": [{"slug": item.slug, "name": _text(item.translations, selected, "name")[0] or item.slug} for item in brands],
        "categories": _flat_categories(index, selected),
    }


def _flat_categories(index: dict[int, Category], locale: str) -> list[dict[str, object]]:
    rows = []
    for category in sorted(
        (item for item in index.values() if item.is_published),
        key=lambda item: (item.sort_order, item.id),
    ):
        parent = index.get(category.parent_id) if category.parent_id is not None else None
        if parent is not None and not parent.is_published:
            continue
        name, _fallback = _text(category.translations, locale, "name")
        rows.append(
            {
                "slug": category.slug,
                "parent_slug": parent.slug if parent is not None else None,
                "name": name or category.slug,
            }
        )
    return rows


@router.get("/products/{slug}")
def product_detail(slug: str, locale: str = Query(), db: Session = Depends(get_db)) -> dict[str, object]:
    selected = _locale(locale)
    product = db.scalar(
        select(Product).where(Product.slug == slug, _published_filter()).options(*_product_options())
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return _detail(product, selected, _categories(db))


def _localized_entries(suffix: str, last_modified: str | None) -> list[dict[str, object]]:
    alternates = {locale: f"/{locale}{suffix}" for locale in LOCALES}
    alternates["x-default"] = alternates["ru"]
    return [
        {"path": alternates[locale], "last_modified": last_modified, "alternates": dict(alternates)}
        for locale in LOCALES
    ]


def _category_suffix(index: dict[int, Category], category: Category) -> str | None:
    path = [item for item in _category_path(index, category) if item.is_published]
    if not path or path[-1].id != category.id or len(path) > 2:
        return None
    if len(path) == 1:
        return f"/categories/{path[0].slug}"
    return f"/categories/{path[0].slug}/{path[1].slug}"


@router.get("/sitemap")
def public_sitemap(db: Session = Depends(get_db)) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    for suffix in ("", "/catalog", "/categories", "/contact"):
        entries.extend(_localized_entries(suffix, None))
    index = _categories(db)
    categories = [
        category
        for category in index.values()
        if category.is_published and _category_suffix(index, category) is not None
    ]
    for category in sorted(categories, key=lambda item: (item.sort_order, item.id)):
        suffix = _category_suffix(index, category)
        if suffix is None:
            continue
        entries.extend(_localized_entries(suffix, _stamp(category.updated_at)))
    brands = _navigable_brands(db)
    for brand in brands:
        entries.extend(_localized_entries(f"/brands/{brand.slug}", _stamp(brand.updated_at)))
    products = db.scalars(
        select(Product).where(_published_filter()).order_by(Product.slug, Product.id)
    ).all()
    for product in products:
        entries.extend(_localized_entries(f"/products/{product.slug}", _stamp(product.updated_at)))
    return {"entries": entries}
