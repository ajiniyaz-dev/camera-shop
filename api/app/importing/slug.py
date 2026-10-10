"""Language-neutral slugs. Import assigns a slug once and does not change it later."""

from __future__ import annotations

import re

# Fixed Russian transliteration for source names. Latin model codes pass through.
_CYRILLIC = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "yo",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}
_NON_SLUG = re.compile(r"[^a-z0-9]+")


def slug_part(value: str) -> str:
    folded = value.casefold()
    transliterated = "".join(_CYRILLIC.get(character, character) for character in folded)
    slug = _NON_SLUG.sub("-", transliterated).strip("-")
    return slug[:80] or "item"


def allocate_slug(base: str, taken: set[str], *, source_row: int | None = None) -> str:
    candidate = base[:180].strip("-") or "item"
    if candidate not in taken:
        taken.add(candidate)
        return candidate
    if source_row is not None:
        suffixed = f"{candidate}-r{source_row}"[:200]
        if suffixed not in taken:
            taken.add(suffixed)
            return suffixed
    number = 2
    while True:
        numbered = f"{candidate}-{number}"[:200]
        if numbered not in taken:
            taken.add(numbered)
            return numbered
        number += 1


def product_slug(
    brand: str | None,
    model: str,
    option: str | None,
    source_row: int,
    taken: set[str],
) -> str:
    parts = [slug_part(brand) if brand else "product", slug_part(model)]
    if option:
        parts.append(slug_part(option))
    return allocate_slug("-".join(parts), taken, source_row=source_row)
