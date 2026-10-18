"""Public UZS display amounts from stored USD and workbook provenance.

The stored ``public_price_amount`` stays USD. This module never writes that column.
The formula is selected by ``product_source_records.source_code``, not by brand.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

SourceCode = Literal["hikvision", "ezviz"]
PriceStatus = Literal["numeric", "on_request", "hidden", "unavailable"]

# 12000 * 0.8 and 12000 * 0.9, written as exact decimals.
HIKVISION_FACTOR = Decimal("9600")
EZVIZ_FACTOR = Decimal("10800")
_FACTORS: dict[str, Decimal] = {
    "hikvision": HIKVISION_FACTOR,
    "ezviz": EZVIZ_FACTOR,
}
_WHOLE_SOM = Decimal("1")


def factor_for_source(source_code: str | None) -> Decimal | None:
    if source_code is None:
        return None
    return _FACTORS.get(source_code)


def usd_to_uzs(stored_usd: Decimal, source_code: str) -> Decimal:
    """Convert one stored USD amount with the workbook formula. Do not call twice."""
    factor = factor_for_source(source_code)
    if factor is None:
        raise ValueError(f"Unknown source code: {source_code}")
    return (stored_usd * factor).quantize(_WHOLE_SOM, rounding=ROUND_HALF_UP)


def public_display_price(
    *,
    public_price_status: str,
    public_price_amount: Decimal | None,
    source_code: str | None,
) -> dict[str, object]:
    """Build the public price object. Currency is UZS when an amount is shown."""
    if public_price_status == "on_request":
        return {"status": "on_request", "amount": None, "currency": None}
    if public_price_status == "hidden":
        return {"status": "hidden", "amount": None, "currency": None}
    if public_price_status != "numeric":
        return {"status": public_price_status, "amount": None, "currency": None}
    if public_price_amount is None:
        return {"status": "unavailable", "amount": None, "currency": None}
    factor = factor_for_source(source_code)
    if factor is None:
        return {"status": "unavailable", "amount": None, "currency": None}
    amount = (public_price_amount * factor).quantize(_WHOLE_SOM, rounding=ROUND_HALF_UP)
    return {"status": "numeric", "amount": format(amount, "f"), "currency": "UZS"}
