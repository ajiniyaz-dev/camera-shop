from app.price_labels import REQUEST_PRICE_LABELS


def test_request_price_labels() -> None:
    assert REQUEST_PRICE_LABELS == {
        "ru": "По запросу",
        "uz": "So'rov asosida",
        "en": "On request",
    }
