/** Labels for the unbranded grouping brand. Keep these aligned with api/app/brand_groups.py. */
const OTHER_BRAND_SLUG = "other";
const OTHER_BRAND_NAMES = new Set(["другие", "boshqalar", "other"]);

export function isOtherBrand(brand: { slug: string; name: string } | null | undefined): boolean {
  if (!brand) {
    return false;
  }
  if (brand.slug === OTHER_BRAND_SLUG) {
    return true;
  }
  return OTHER_BRAND_NAMES.has(brand.name.trim().replace(/\s+/g, " ").toLowerCase());
}

/** Structured manufacturer data. The grouping brand is a label, not a manufacturer. */
export function schemaBrand(
  brand: { slug: string; name: string } | null | undefined,
): { "@type": "Brand"; name: string } | null {
  if (!brand || isOtherBrand(brand)) {
    return null;
  }
  return { "@type": "Brand", name: brand.name };
}
