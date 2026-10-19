"""Locale-aware public image alt helpers (no database)."""

from app.public.router import _image_alt


def test_image_alt_prefers_non_cyrillic_locale_name() -> None:
    assert _image_alt(None, "Flexible transition") == "Flexible transition"
    assert _image_alt("", "Flexible transition") == "Flexible transition"
    assert _image_alt("Front", "Flexible transition") == "Front"
    assert _image_alt("гибкий переход", "Flexible transition") == "Flexible transition"
    assert _image_alt("гибкий переход", "Egiluvchan o‘tish") == "Egiluvchan o‘tish"


def test_image_alt_keeps_cyrillic_when_locale_name_is_cyrillic() -> None:
    assert _image_alt("гибкий переход", "гибкий переход") == "гибкий переход"
    assert _image_alt("гибкий переход", "Купольная") == "гибкий переход"
    assert _image_alt("Брелок", "Брелок") == "Брелок"
