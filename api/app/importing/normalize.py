"""Deterministic text, price, brand, and match-key rules."""

from __future__ import annotations

import hashlib
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

_DASHES = str.maketrans(
    {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\ufe58": "-",
        "\ufe63": "-",
        "\uff0d": "-",
    }
)
_KEY_SEPARATOR = "\x1f"
_REQUEST_PRICE = "по запросу"
_BRAND_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("HiLook", re.compile(r"hilook", re.IGNORECASE)),
    ("Hikvision", re.compile(r"hikvision", re.IGNORECASE)),
    ("Seagate", re.compile(r"seagate", re.IGNORECASE)),
    ("WD", re.compile(r"(?<!\w)wd(?!\w)", re.IGNORECASE)),
    ("Andel", re.compile(r"andel", re.IGNORECASE)),
    ("Cougar", re.compile(r"cougar", re.IGNORECASE)),
)
_CENTS = Decimal("0.01")


def collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def normalize_header(value: str) -> str:
    return collapse_whitespace(value).casefold()


def display_model(value: str) -> str:
    return collapse_whitespace(value).strip()


def normalize_model(display: str) -> str:
    """Case-fold the display model and fold Unicode dashes for the match key."""

    return display.casefold().translate(_DASHES)


def normalize_option(value: str | None) -> str:
    if value is None:
        return ""
    collapsed = collapse_whitespace(value).strip()
    if not collapsed:
        return ""
    return collapsed.casefold()


def trim_description(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def description_sha256(description: str | None) -> str:
    return sha256_text(description or "")


def build_match_key(
    source_code: str,
    worksheet: str,
    model_normalized: str,
    option_normalized: str,
    description_digest: str,
) -> str:
    """Join identity parts with a unit separator so worksheet text cannot collide."""

    return _KEY_SEPARATOR.join(
        (source_code, worksheet, model_normalized, option_normalized, description_digest)
    )


def filename_hint(filename: str) -> str | None:
    lowered = filename.casefold()
    ezviz = "ezviz" in lowered
    hikvision = "hikvision" in lowered
    if ezviz and not hikvision:
        return "ezviz"
    if hikvision and not ezviz:
        return "hikvision"
    return None


def is_service_option(option: str | None) -> bool:
    if option is None:
        return False
    folded = option.strip().casefold()
    return folded.startswith("ежемесячно:") or folded.startswith("ежегодно:")


def is_cloud_history_model(model: str) -> bool:
    return "видеоистория" in model.casefold()


def detect_brands(*parts: str | None) -> list[str]:
    """Return verified brand names found in model or description text.

    The worksheet name is not consulted. More than one name means the row is ambiguous.
    """

    text = "\n".join(part for part in parts if part)
    if not text:
        return []
    found: list[str] = []
    for name, pattern in _BRAND_PATTERNS:
        if pattern.search(text) and name not in found:
            found.append(name)
    return found


def decimal_amount(value: int | float | Decimal) -> Decimal | None:
    """Convert a numeric cell to cents without treating it as a binary price."""

    if isinstance(value, bool):
        return None
    try:
        if isinstance(value, Decimal):
            amount = value
        elif isinstance(value, int):
            amount = Decimal(value)
        elif isinstance(value, float):
            amount = Decimal(str(value))
        else:
            return None
        if not amount.is_finite():
            return None
    except (InvalidOperation, ValueError):
        return None
    quantized = amount.quantize(_CENTS, rounding=ROUND_HALF_UP)
    if quantized < 0 or quantized.copy_abs() >= Decimal("10000000000"):
        return None
    return quantized


def format_amount(amount: Decimal) -> str:
    return f"{amount:.2f}"


def is_numeric_value(value: object) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float, Decimal)):
        return True
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return False
        try:
            Decimal(stripped)
        except InvalidOperation:
            return False
        return True
    return False


def number_text(value: object) -> str | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        decimal = decimal_amount(value)
        if decimal is None:
            return str(value)
        if decimal == decimal.to_integral():
            return str(int(decimal))
        return format_amount(decimal)
    if isinstance(value, Decimal):
        return format(value, "f")
    return None


def classify_price(value: object, *, missing_cache: bool) -> dict[str, object]:
    """Map one price cell to source kind and the public proposal."""

    if missing_cache:
        return {
            "kind": "invalid",
            "raw": None,
            "amount": None,
            "public_status": None,
            "public_amount": None,
            "currency": None,
            "issue": "formula_without_cache",
        }
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return _on_request("blank", None)
    if isinstance(value, str):
        if value.strip().casefold() == _REQUEST_PRICE:
            return _on_request("explicit_on_request", value)
        return {
            "kind": "invalid",
            "raw": value,
            "amount": None,
            "public_status": None,
            "public_amount": None,
            "currency": None,
            "issue": "unexpected_price_text",
        }
    amount = decimal_amount(value) if isinstance(value, (int, float, Decimal)) else None
    if amount is None:
        return {
            "kind": "invalid",
            "raw": number_text(value),
            "amount": None,
            "public_status": None,
            "public_amount": None,
            "currency": None,
            "issue": "unexpected_price_text",
        }
    return {
        "kind": "numeric",
        "raw": number_text(value),
        "amount": format_amount(amount),
        "public_status": "numeric",
        "public_amount": format_amount(amount),
        "currency": "USD",
        "issue": None,
    }


def _on_request(kind: str, raw: str | None) -> dict[str, object]:
    return {
        "kind": kind,
        "raw": raw,
        "amount": None,
        "public_status": "on_request",
        "public_amount": None,
        "currency": None,
        "issue": None,
    }
