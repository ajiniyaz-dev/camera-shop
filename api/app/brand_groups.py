"""Recognise the unbranded grouping brand without giving it a special database status.

Other is an ordinary ``brands`` row. An administrator creates that row. Import
matching does not create it and does not use its name as a manufacturer.
"""

from __future__ import annotations

OTHER_BRAND_SLUG = "other"

# Display names an administrator stores on the brand. They are labels for the
# group, not a manufacturer. The same spellings are recognised by the public site.
OTHER_BRAND_NAMES = ("Другие", "Boshqalar", "Other")


def is_other_brand_name(name: str | None) -> bool:
    if name is None:
        return False
    folded = " ".join(name.split()).casefold()
    if not folded:
        return False
    return folded in {item.casefold() for item in OTHER_BRAND_NAMES}


def is_other_brand(slug: str | None, names: list[str] | tuple[str, ...] | None = None) -> bool:
    if slug == OTHER_BRAND_SLUG:
        return True
    return any(is_other_brand_name(name) for name in names or ())
