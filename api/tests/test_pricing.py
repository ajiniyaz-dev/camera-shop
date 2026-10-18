"""Unit tests for the public UZS display formula. No database writes."""

from decimal import Decimal

from app.pricing import (
    EZVIZ_FACTOR,
    HIKVISION_FACTOR,
    factor_for_source,
    public_display_price,
    usd_to_uzs,
)


def test_factors_match_the_client_formulas() -> None:
    assert HIKVISION_FACTOR == Decimal("12000") * Decimal("0.8")
    assert EZVIZ_FACTOR == Decimal("12000") * Decimal("0.9")
    assert factor_for_source("hikvision") == HIKVISION_FACTOR
    assert factor_for_source("ezviz") == EZVIZ_FACTOR
    assert factor_for_source(None) is None
    assert factor_for_source("other") is None


def test_workbook_examples_and_hilook_use_source_code() -> None:
    assert usd_to_uzs(Decimal("500"), "hikvision") == Decimal("4800000")
    assert usd_to_uzs(Decimal("500"), "ezviz") == Decimal("5400000")
    # Hilook sheet in the Hikvision workbook uses the Hikvision factor.
    assert usd_to_uzs(Decimal("115"), "hikvision") == Decimal("1104000")
    assert public_display_price(
        public_price_status="numeric",
        public_price_amount=Decimal("115.00"),
        source_code="hikvision",
    ) == {"status": "numeric", "amount": "1104000", "currency": "UZS"}


def test_half_up_rounding_and_decimal_precision() -> None:
    # 0.005 * 9600 = 48 exactly; a half-up edge stays a whole soʻm.
    assert usd_to_uzs(Decimal("0.01"), "hikvision") == Decimal("96")
    assert usd_to_uzs(Decimal("0.15"), "hikvision") == Decimal("1440")
    assert usd_to_uzs(Decimal("92.50"), "ezviz") == Decimal("999000")
    # Binary floats would drift; Decimal keeps 20.50 * 9600 exact.
    assert usd_to_uzs(Decimal("20.50"), "hikvision") == Decimal("196800")


def test_on_request_and_hidden_stay_without_amounts() -> None:
    assert public_display_price(
        public_price_status="on_request",
        public_price_amount=None,
        source_code="hikvision",
    ) == {"status": "on_request", "amount": None, "currency": None}
    assert public_display_price(
        public_price_status="hidden",
        public_price_amount=Decimal("5.00"),
        source_code="ezviz",
    ) == {"status": "hidden", "amount": None, "currency": None}


def test_missing_amount_and_unknown_provenance_are_unavailable() -> None:
    assert public_display_price(
        public_price_status="numeric",
        public_price_amount=None,
        source_code="hikvision",
    ) == {"status": "unavailable", "amount": None, "currency": None}
    assert public_display_price(
        public_price_status="numeric",
        public_price_amount=Decimal("30.00"),
        source_code=None,
    ) == {"status": "unavailable", "amount": None, "currency": None}
    assert public_display_price(
        public_price_status="numeric",
        public_price_amount=Decimal("30.00"),
        source_code="unknown",
    ) == {"status": "unavailable", "amount": None, "currency": None}


def test_conversion_is_not_applied_twice() -> None:
    first = usd_to_uzs(Decimal("500"), "hikvision")
    assert first == Decimal("4800000")
    # Applying the factor again would invent 46,080,000,000.
    assert first * HIKVISION_FACTOR == Decimal("46080000000")
    again = public_display_price(
        public_price_status="numeric",
        public_price_amount=Decimal("500.00"),
        source_code="hikvision",
    )
    assert again["amount"] == "4800000"
    assert again["currency"] == "UZS"
