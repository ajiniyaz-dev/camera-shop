"""Apply one approved preview job. A repeated call after success does not write again.

Catalog changes and the ``applied`` status commit in one database transaction.
Image files are already stored by checksum during staging. This service only
points catalog rows at those keys. A failed transaction does not delete a
checksum that another job or product might share. Workbook copies under
``imports/{job_id}/`` are private staging files, not public media.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.importing.slug import allocate_slug, product_slug, slug_part
from app.models import (
    AdminAuditLog,
    Brand,
    BrandTranslation,
    Category,
    CategoryTranslation,
    ImportAsset,
    ImportFile,
    ImportJob,
    ImportRow,
    Product,
    ProductImage,
    ProductSourceRecord,
    ProductTranslation,
)

_BLOCKING_ACTIONS = {"insert", "update", "possible_match", "conflict"}


class ApplyError(Exception):
    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def apply_job(
    session: Session,
    job_id: int,
    admin_id: int,
    media_root: Path,
    *,
    ip_address: str | None = None,
) -> dict[str, Any]:
    job = session.scalar(select(ImportJob).where(ImportJob.id == job_id).with_for_update())
    if job is None:
        raise ApplyError("Import job not found.", status_code=404)
    if job.status == "applied":
        return _public_job(job)
    if job.status != "preview":
        raise ApplyError("This import job cannot be applied.", status_code=409)
    files = _included_files(session, job.id)
    if not files:
        raise ApplyError("This import job has no validated workbook to apply.", status_code=409)
    rows = _rows_for(session, [file.id for file in files])
    blockers = blocking_rows(rows)
    if blockers:
        raise ApplyError("Resolve blocking rows before applying this import.", status_code=409)

    now = datetime.now(timezone.utc)
    brands = _BrandBook(session)
    categories = _CategoryBook(session, publish=job.publish_new_products)
    taken_slugs = set(session.scalars(select(Product.slug)).all())
    excluded_assets = set((job.summary or {}).get("excluded_asset_ids") or [])
    touched_products: set[int] = set()
    counts = {"inserted": 0, "updated": 0, "unchanged": 0, "excluded": 0, "images_linked": 0}
    source_codes = {file.source_code for file in files}

    for row in rows:
        if row.action in {"skip", "exclude"} or row.classification in {"blank", "stray", "invalid"}:
            counts["excluded"] += 1
            continue
        if row.classification == "heading":
            _ensure_heading_category(session, categories, row)
            continue
        if row.resolution == "keep_current" and row.action in {"insert", "possible_match", "conflict"}:
            counts["excluded"] += 1
            if row.action == "possible_match" and row.matched_product_id is not None:
                touched_products.add(row.matched_product_id)
            row.applied = row.action != "conflict"
            continue
        if row.action == "conflict":
            counts["excluded"] += 1
            continue
        if row.action == "insert":
            product = _insert_product(session, row, job, brands, categories, taken_slugs, now)
            _refresh_source(session, product, row, job, now, creating=True)
            linked = _link_images(session, product, row, job, media_root, excluded_assets, now)
            counts["images_linked"] += linked
            counts["inserted"] += 1
            row.matched_product_id = product.id
            row.applied = True
            touched_products.add(product.id)
            continue
        product = session.get(Product, row.matched_product_id)
        if product is None:
            raise ApplyError("A staged row no longer matches a catalog product.", status_code=409)
        if row.action == "unchanged" or _writes_nothing(row):
            counts["unchanged"] += 1
        else:
            _update_product(product, row, brands, categories, now)
            counts["updated"] += 1
        _refresh_source(session, product, row, job, now, creating=False)
        linked = _link_images(session, product, row, job, media_root, excluded_assets, now)
        counts["images_linked"] += linked
        row.applied = True
        touched_products.add(product.id)

    absent = _mark_absent(session, source_codes, touched_products, now)
    result = {
        "status": "applied",
        "counts": counts,
        "absent_products": absent,
        "sources": sorted(source_codes),
    }
    previous = dict(job.summary or {})
    previous["result"] = result
    job.summary = previous
    job.status = "applied"
    job.approved_by = admin_id
    job.applied_at = now
    job.error_message = None
    session.add(
        AdminAuditLog(
            actor_id=admin_id,
            action="import_applied",
            entity_type="import_job",
            entity_id=job.id,
            detail={"result": "applied", "counts": counts, "absent_products": absent},
            ip_address=(ip_address or "")[:128] or None,
        )
    )
    session.flush()
    return _public_job(job)


def mark_job_failed(session: Session, job_id: int) -> None:
    """Persist a failure only when the apply transaction rolled back to preview."""

    job = session.scalar(select(ImportJob).where(ImportJob.id == job_id).with_for_update())
    if job is None or job.status != "preview":
        return
    job.status = "failed"
    job.error_message = "The import could not be applied."
    session.flush()


def blocking_rows(rows: list[ImportRow]) -> list[int]:
    blocked: list[int] = []
    for row in rows:
        if row.classification == "invalid" and row.action != "exclude":
            blocked.append(row.id)
            continue
        if row.action in _BLOCKING_ACTIONS and row.resolution == "pending":
            blocked.append(row.id)
            continue
        if row.action in {"update", "unchanged", "possible_match"} and row.resolution in {
            "accept_excel",
            "accept_new",
        }:
            if row.matched_product_id is None:
                blocked.append(row.id)
    return blocked


def _included_files(session: Session, job_id: int) -> list[ImportFile]:
    return list(
        session.scalars(
            select(ImportFile).where(
                ImportFile.job_id == job_id,
                ImportFile.included_in_apply.is_(True),
                ImportFile.validation_status == "valid",
            )
        ).all()
    )


def _rows_for(session: Session, file_ids: list[int]) -> list[ImportRow]:
    if not file_ids:
        return []
    return list(
        session.scalars(
            select(ImportRow)
            .where(ImportRow.import_file_id.in_(file_ids))
            .order_by(ImportRow.import_file_id, ImportRow.worksheet_name, ImportRow.source_row)
        ).all()
    )


def _writes_nothing(row: ImportRow) -> bool:
    if row.resolution == "keep_current":
        resolutions = (row.proposal or {}).get("field_resolutions") or {}
        return all(value == "keep_current" for value in resolutions.values()) or not resolutions
    changes = (row.proposal or {}).get("field_changes") or []
    return row.action == "unchanged" or not changes


def _accepts_field(row: ImportRow, field_name: str) -> bool:
    if row.resolution == "keep_current":
        decision = ((row.proposal or {}).get("field_resolutions") or {}).get(field_name, "keep_current")
        return decision in {"accept_excel", "accept_new"}
    if row.resolution in {"accept_excel", "accept_new"}:
        decision = ((row.proposal or {}).get("field_resolutions") or {}).get(field_name, "accept_excel")
        return decision != "keep_current"
    return False


def _insert_product(
    session: Session,
    row: ImportRow,
    job: ImportJob,
    brands: _BrandBook,
    categories: _CategoryBook,
    taken_slugs: set[str],
    now: datetime,
) -> Product:
    proposal = row.proposal
    price = proposal["price"]
    status, amount, currency = _public_price(price)
    brand_id = brands.ensure(proposal.get("brand"), job.publish_new_products)
    category_id = categories.ensure(
        proposal.get("category_name"),
        proposal.get("parent_section_label"),
        _file_source(session, row),
        row.worksheet_name,
    )
    product = Product(
        brand_id=brand_id,
        category_id=category_id,
        product_kind=proposal.get("product_kind") or "product",
        model_raw=proposal.get("model_raw") or proposal["model_display"],
        model_display=proposal["model_display"],
        model_normalized=proposal["model_normalized"],
        option_label=proposal.get("option_label"),
        public_price_status=status,
        public_price_amount=amount,
        public_currency=currency,
        stock_status="in_stock",
        slug=product_slug(
            proposal.get("brand"),
            proposal["model_display"],
            proposal.get("option_label"),
            row.source_row,
            taken_slugs,
        ),
        catalog_status="published" if job.publish_new_products else "draft",
        price_updated_at=now,
    )
    session.add(product)
    session.flush()
    session.add(
        ProductTranslation(
            product_id=product.id,
            locale="ru",
            description=proposal.get("description"),
            origin="source",
            description_locked=False,
        )
    )
    session.flush()
    return product


def _update_product(
    product: Product,
    row: ImportRow,
    brands: _BrandBook,
    categories: _CategoryBook,
    now: datetime,
) -> None:
    proposal = row.proposal
    if _accepts_field(row, "model_display"):
        product.model_display = proposal["model_display"]
        product.model_normalized = proposal["model_normalized"]
        product.model_raw = proposal.get("model_raw") or proposal["model_display"]
    if _accepts_field(row, "option_label"):
        product.option_label = proposal.get("option_label")
    if _accepts_field(row, "public_price") and product.public_price_status != "hidden":
        status, amount, currency = _public_price(proposal["price"])
        changed = (
            product.public_price_status != status
            or product.public_price_amount != amount
            or product.public_currency != currency
        )
        product.public_price_status = status
        product.public_price_amount = amount
        product.public_currency = currency
        if changed:
            product.price_updated_at = now
    if _accepts_field(row, "description"):
        translation = next((item for item in product.translations if item.locale == "ru"), None)
        if translation is None:
            product.translations.append(
                ProductTranslation(
                    locale="ru",
                    description=proposal.get("description"),
                    origin="source",
                )
            )
        else:
            translation.description = proposal.get("description")
    if _accepts_field(row, "brand"):
        product.brand_id = brands.ensure(proposal.get("brand"), False)
    if _accepts_field(row, "category"):
        product.category_id = categories.ensure(
            proposal.get("category_name"),
            proposal.get("parent_section_label"),
            product.source_record.source_code if product.source_record is not None else proposal.get("source_code"),
            row.worksheet_name,
        )


def _refresh_source(
    session: Session,
    product: Product,
    row: ImportRow,
    job: ImportJob,
    now: datetime,
    *,
    creating: bool,
) -> None:
    proposal = row.proposal
    price = proposal["price"]
    amount = Decimal(str(price["amount"])) if price.get("amount") is not None else None
    record = product.source_record
    workbook_name = _workbook_name(session, row)
    if record is None:
        record = ProductSourceRecord(
            product_id=product.id,
            source_code=proposal["source_code"],
            source_workbook=workbook_name,
            source_worksheet=row.worksheet_name,
            source_row=row.source_row,
            source_model_raw=proposal.get("model_raw") or proposal["model_display"],
            source_price_kind=price["kind"],
            match_key=proposal["match_key"],
            first_job_id=job.id,
            last_job_id=job.id,
        )
        session.add(record)
    elif creating:
        raise ApplyError("The catalog already has a source mapping for this product.", status_code=409)
    record.source_workbook = workbook_name
    record.source_worksheet = row.worksheet_name
    record.source_row = row.source_row
    record.source_line_number = proposal.get("line_number")
    record.source_model_raw = proposal.get("model_raw") or proposal["model_display"]
    record.source_option_raw = proposal.get("option_label")
    record.source_description_raw = proposal.get("description")
    record.source_description_sha256 = proposal.get("description_sha256")
    record.source_price_header = price.get("header")
    record.source_price_raw = price.get("raw") if isinstance(price.get("raw"), str) else None
    record.source_price_kind = price["kind"]
    record.source_price_amount = amount
    record.section_label = proposal.get("section_label")
    record.parent_section_label = proposal.get("parent_section_label")
    record.internal_note = proposal.get("internal_note")
    record.match_key = proposal["match_key"]
    record.last_job_id = job.id
    record.last_seen_at = now
    record.absent_from_latest = False
    session.flush()


def _link_images(
    session: Session,
    product: Product,
    row: ImportRow,
    job: ImportJob,
    media_root: Path,
    excluded_assets: set[int],
    now: datetime,
) -> int:
    del now
    wanted = [
        image
        for image in (row.proposal or {}).get("images") or []
        if image.get("link_status") == "linked_high" and not image.get("excluded")
    ]
    if not wanted:
        return 0
    assets = list(
        session.scalars(
            select(ImportAsset).where(
                ImportAsset.import_file_id == row.import_file_id,
                ImportAsset.link_status == "linked_high",
                ImportAsset.worksheet == row.worksheet_name,
            )
        ).all()
    )
    existing = {image.sha256.strip() for image in product.images}
    has_primary = any(image.is_primary and image.association_status != "rejected" for image in product.images)
    sort_order = max((image.sort_order for image in product.images), default=-1)
    linked = 0
    for spec in wanted:
        digest = str(spec.get("sha256") or "")
        asset = next((item for item in assets if item.sha256.strip() == digest and item.anchor_row == row.source_row), None)
        if asset is None or asset.id in excluded_assets or digest in existing:
            continue
        path = (media_root / asset.object_key).resolve()
        if media_root.resolve() not in path.parents or not path.is_file():
            continue
        sort_order += 1
        primary = not has_primary
        has_primary = has_primary or primary
        session.add(
            ProductImage(
                product_id=product.id,
                storage_backend="local",
                object_key=asset.object_key,
                mime_type=asset.mime_type,
                byte_size=path.stat().st_size,
                sha256=digest,
                sort_order=sort_order,
                is_primary=primary,
                alt_text=_alt_text(row),
                association_status="high",
                source_code=row.proposal.get("source_code"),
                source_worksheet=row.worksheet_name,
                anchor_row=asset.anchor_row,
                anchor_col=asset.anchor_col,
                anchor_to_row=asset.anchor_to_row,
            )
        )
        existing.add(digest)
        linked += 1
    return linked


def _mark_absent(session: Session, source_codes: set[str], touched: set[int], now: datetime) -> int:
    if not source_codes:
        return 0
    records = list(
        session.scalars(
            select(ProductSourceRecord).where(ProductSourceRecord.source_code.in_(source_codes))
        ).all()
    )
    absent = 0
    for record in records:
        if record.product_id in touched:
            continue
        if not record.absent_from_latest:
            record.absent_from_latest = True
            record.last_seen_at = now
            absent += 1
    return absent


def _public_price(price: dict[str, Any]) -> tuple[str, Decimal | None, str | None]:
    if price.get("kind") == "numeric" and price.get("amount") is not None:
        return "numeric", Decimal(str(price["amount"])).quantize(Decimal("0.01")), "USD"
    return "on_request", None, None


def _alt_text(row: ImportRow) -> str:
    brand = row.proposal.get("brand")
    model = row.proposal.get("model_display") or ""
    text = f"{brand} {model}".strip() if brand else model
    return text[:300]


def _file_source(session: Session, row: ImportRow) -> str:
    return row.proposal.get("source_code") or ""


def _workbook_name(session: Session, row: ImportRow) -> str:
    file = session.get(ImportFile, row.import_file_id)
    return file.original_filename if file is not None else "workbook.xlsx"


def _ensure_heading_category(session: Session, categories: _CategoryBook, row: ImportRow) -> None:
    proposal = (row.proposal or {}).get("category_proposal") or {}
    name = proposal.get("name")
    if not name:
        return
    file = session.get(ImportFile, row.import_file_id)
    categories.ensure(
        name,
        proposal.get("parent_name"),
        file.source_code if file is not None else "",
        row.worksheet_name,
    )


def _public_job(job: ImportJob) -> dict[str, Any]:
    summary = job.summary or {}
    return {
        "id": job.id,
        "status": job.status,
        "replace_prices": job.replace_prices,
        "publish_new_products": job.publish_new_products,
        "approved_by": job.approved_by,
        "applied_at": job.applied_at.isoformat() if job.applied_at else None,
        "error_message": job.error_message,
        "summary": summary,
    }


class _BrandBook:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.by_name: dict[str, Brand] = {}
        rows = session.scalars(select(Brand).options(selectinload(Brand.translations))).all()
        for brand in rows:
            for translation in brand.translations:
                if translation.locale == "ru":
                    self.by_name[translation.name] = brand
        self.slugs = {brand.slug for brand in rows}

    def ensure(self, name: str | None, publish: bool) -> int | None:
        if not name:
            return None
        found = self.by_name.get(name)
        if found is not None:
            return found.id
        brand = Brand(slug=allocate_slug(slug_part(name), self.slugs), is_published=publish)
        self.session.add(brand)
        self.session.flush()
        self.session.add(BrandTranslation(brand_id=brand.id, locale="ru", name=name))
        self.by_name[name] = brand
        return brand.id


class _CategoryBook:
    def __init__(self, session: Session, *, publish: bool) -> None:
        self.session = session
        self.publish = publish
        self.rows = list(session.scalars(select(Category).options(selectinload(Category.translations))).all())
        self.slugs: set[tuple[int, str]] = {(category.parent_id or 0, category.slug) for category in self.rows}

    def ensure(
        self,
        name: str | None,
        parent_name: str | None,
        source_code: str,
        worksheet: str,
    ) -> int | None:
        if not name:
            return None
        parent_id = None
        if parent_name and parent_name != name:
            parent_id = self.ensure(parent_name, None, source_code, worksheet)
        found = self._find(name, parent_id, source_code, worksheet)
        if found is not None:
            return found.id
        sibling_slugs = {item for parent, item in self.slugs if parent == (parent_id or 0)}
        slug = allocate_slug(slug_part(name), sibling_slugs)
        self.slugs.add((parent_id or 0, slug))
        category = Category(
            parent_id=parent_id,
            slug=slug,
            source_code=source_code or None,
            source_worksheet=worksheet,
            source_heading=name,
            sort_order=len(self.rows),
            is_published=self.publish,
        )
        self.session.add(category)
        self.session.flush()
        translation = CategoryTranslation(category_id=category.id, locale="ru", name=name)
        category.translations.append(translation)
        self.session.add(translation)
        self.rows.append(category)
        return category.id

    def _find(self, name: str, parent_id: int | None, source_code: str, worksheet: str) -> Category | None:
        for category in self.rows:
            if category.parent_id != parent_id:
                continue
            if category.source_code != (source_code or None) or category.source_worksheet != worksheet:
                continue
            if any(item.locale == "ru" and item.name == name for item in category.translations):
                return category
        return None
