"""Match staged rows to existing source records. This does not write the catalog."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.importing.normalize import normalize_option
from app.importing.parse import ParsedRow

_LOCKED_FIELDS = {
    "model_display": "model_locked",
    "option_label": "option_locked",
    "public_price": "price_locked",
    "description": "description_locked",
    "brand": "brand_locked",
    "category": "category_locked",
}


@dataclass(frozen=True)
class ExistingSource:
    product_id: int
    match_key: str
    worksheet: str
    model_normalized: str
    option_label: str | None
    model_display: str
    description: str | None
    public_price_status: str
    public_price_amount: Decimal | None
    public_currency: str | None
    source_price_kind: str
    brand_name: str | None
    category_name: str | None
    price_locked: bool
    option_locked: bool
    brand_locked: bool
    category_locked: bool
    model_locked: bool
    description_locked: bool


def match_rows(
    rows: list[ParsedRow],
    existing: list[ExistingSource],
    *,
    replace_prices: bool,
) -> list[int]:
    """Set action, resolution, and match fields. Return product ids absent from this file."""

    for row in rows:
        if row.classification == "invalid":
            row.action = "exclude"
            row.resolution = "pending"
            row.matched_product_id = None
        elif row.classification not in {"product", "service"}:
            row.action = "skip"
            row.resolution = "pending"
            row.matched_product_id = None

    candidates = [row for row in rows if row.classification in {"product", "service"}]
    by_key: dict[str, list[ExistingSource]] = {}
    for record in existing:
        by_key.setdefault(record.match_key, []).append(record)

    incoming_keys: dict[str, list[ParsedRow]] = {}
    for row in candidates:
        incoming_keys.setdefault(str(row.proposal["match_key"]), []).append(row)

    matched_ids: set[int] = set()
    unresolved: list[ParsedRow] = []
    for row in candidates:
        key = str(row.proposal["match_key"])
        if len(incoming_keys[key]) > 1:
            _conflict(row, "duplicate_match_key")
            continue
        found = by_key.get(key, [])
        if len(found) > 1:
            _conflict(row, "duplicate_match_key")
            continue
        if len(found) == 1:
            _compare(row, found[0], replace_prices=replace_prices)
            matched_ids.add(found[0].product_id)
            continue
        unresolved.append(row)

    consumed = {record.product_id for record in existing if record.product_id in matched_ids}
    grouped: dict[tuple[str, str, str], list[ParsedRow]] = {}
    for row in unresolved:
        grouped.setdefault(_pair_key(row), []).append(row)
    existing_grouped: dict[tuple[str, str, str], list[ExistingSource]] = {}
    for record in existing:
        if record.product_id in consumed:
            continue
        existing_grouped.setdefault(_existing_pair(record), []).append(record)

    for pair, incoming in grouped.items():
        found = existing_grouped.get(pair, [])
        if len(incoming) == 1 and len(found) == 1:
            row = incoming[0]
            _compare(row, found[0], replace_prices=replace_prices)
            row.action = "possible_match"
            row.resolution = "pending"
            row.messages.append({"code": "possible_match"})
            row.messages = _sorted_messages(row.messages)
            matched_ids.add(found[0].product_id)
            continue
        for row in incoming:
            row.action = "insert"
            row.resolution = "accept_new"
            row.matched_product_id = None
            row.proposal["field_resolutions"] = {"excel": "accept_new"}
            row.proposal["field_changes"] = []

    _warn_duplicate_models(candidates)
    return sorted(record.product_id for record in existing if record.product_id not in matched_ids)


def _compare(row: ParsedRow, record: ExistingSource, *, replace_prices: bool) -> None:
    changes: list[str] = []
    resolutions: dict[str, str] = {}
    proposal = row.proposal
    if proposal["model_display"] != record.model_display:
        changes.append("model_display")
    if proposal["option_label"] != record.option_label:
        changes.append("option_label")
    if _description(proposal) != _clean(record.description):
        changes.append("description")
    if proposal["brand"] != record.brand_name:
        changes.append("brand")
    if proposal["category_name"] != record.category_name:
        changes.append("category")
    if _price_differs(proposal, record):
        changes.append("public_price")
    elif str(proposal["price"]["kind"]) != record.source_price_kind:
        changes.append("source_price_kind")

    locked_kept = False
    for field_name in changes:
        if field_name == "source_price_kind":
            resolutions[field_name] = "accept_excel"
            continue
        if field_name == "public_price" and record.public_price_status == "hidden":
            resolutions[field_name] = "keep_current"
            row.messages.append({"code": "hidden_price_preserved"})
            locked_kept = True
            continue
        lock_name = _LOCKED_FIELDS[field_name]
        locked = bool(getattr(record, lock_name))
        if field_name == "public_price" and locked and replace_prices:
            resolutions[field_name] = "accept_excel"
            row.messages.append({"code": "replace_prices"})
            continue
        if locked:
            resolutions[field_name] = "keep_current"
            locked_kept = True
            continue
        resolutions[field_name] = "accept_excel"

    proposal["field_changes"] = changes
    proposal["field_resolutions"] = resolutions
    row.matched_product_id = record.product_id
    if not changes:
        row.action = "unchanged"
        row.resolution = "accept_excel"
    else:
        row.action = "update"
        row.resolution = "keep_current" if locked_kept else "accept_excel"
    row.messages = _sorted_messages(row.messages)


def _conflict(row: ParsedRow, code: str) -> None:
    row.action = "conflict"
    row.resolution = "pending"
    row.matched_product_id = None
    row.proposal["field_changes"] = []
    row.proposal["field_resolutions"] = {}
    row.messages.append({"code": code})
    row.messages = _sorted_messages(row.messages)


def _warn_duplicate_models(rows: list[ParsedRow]) -> None:
    grouped: dict[str, list[ParsedRow]] = {}
    for row in rows:
        grouped.setdefault(str(row.proposal["model_normalized"]), []).append(row)
    for group in grouped.values():
        keys = {str(row.proposal["match_key"]) for row in group}
        if len(group) < 2 or len(keys) < 2:
            continue
        for row in group:
            if row.action == "conflict":
                continue
            row.messages.append({"code": "duplicate_model"})
            row.messages = _sorted_messages(row.messages)


def _pair_key(row: ParsedRow) -> tuple[str, str, str]:
    proposal = row.proposal
    return (
        str(proposal["worksheet"]),
        str(proposal["model_normalized"]),
        str(proposal["option_normalized"]),
    )


def _existing_pair(record: ExistingSource) -> tuple[str, str, str]:
    return (record.worksheet, record.model_normalized, normalize_option(record.option_label))


def _price_differs(proposal: dict[str, Any], record: ExistingSource) -> bool:
    price = proposal["price"]
    status = price["public_status"]
    amount = price["public_amount"]
    currency = price["currency"]
    if record.public_price_status != status:
        return True
    if (record.public_currency or None) != currency:
        return True
    if amount is None:
        return record.public_price_amount is not None
    if record.public_price_amount is None:
        return True
    return Decimal(str(amount)) != Decimal(record.public_price_amount)


def _description(proposal: dict[str, Any]) -> str | None:
    return _clean(proposal.get("description"))


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _sorted_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    ordered: list[dict[str, Any]] = []
    for message in sorted(messages, key=lambda item: str(item.get("code"))):
        code = str(message.get("code"))
        if code in seen:
            continue
        seen.add(code)
        ordered.append({"code": code})
    return ordered
