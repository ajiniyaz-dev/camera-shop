const CYRILLIC = /[А-Яа-яЁё]/;

function categoryHref(locale: string, slug: string, parentSlug: string | null): string {
  if (parentSlug) return `/${locale}/categories/${parentSlug}/${slug}`;
  return `/${locale}/categories/${slug}`;
}

export type CatalogLink = {
  kind: "brand" | "category";
  href: string;
  name: string;
};

export function showOriginalNote(fallback: boolean, text: string | null | undefined): boolean {
  if (!fallback || !text?.trim()) return false;
  return CYRILLIC.test(text);
}

export function billingPeriod(option: string | null | undefined): "monthly" | "yearly" | null {
  const key = option?.trim().toLowerCase().replace(/:$/, "") ?? "";
  if (key === "ежемесячно") return "monthly";
  if (key === "ежегодно") return "yearly";
  return null;
}

export function isServicePlan(product: {
  product_kind?: string | null;
  option_label?: string | null;
}): boolean {
  if (product.product_kind === "service") return true;
  if (product.product_kind === "product") return false;
  return billingPeriod(product.option_label) !== null;
}

export function catalogDestinations(
  locale: string,
  brand: { slug: string; name: string } | null | undefined,
  category: { slug: string; parent_slug: string | null; name: string } | null | undefined,
): CatalogLink[] {
  const links: CatalogLink[] = [];
  if (brand?.slug && brand.name) {
    links.push({ kind: "brand", href: `/${locale}/brands/${brand.slug}`, name: brand.name });
  }
  if (category?.slug && category.name) {
    links.push({
      kind: "category",
      href: categoryHref(locale, category.slug, category.parent_slug),
      name: category.name,
    });
  }
  const seen = new Set<string>();
  return links.filter((link) => {
    if (seen.has(link.href)) return false;
    seen.add(link.href);
    return true;
  });
}

export function listingHasActiveFilter(query: {
  q?: string;
  minPrice?: string;
  maxPrice?: string;
  brand?: string;
  category?: string;
  lockedBrand?: boolean;
  lockedCategory?: boolean;
}): boolean {
  if (query.q || query.minPrice || query.maxPrice) return true;
  if (query.brand && !query.lockedBrand) return true;
  if (query.category && !query.lockedCategory) return true;
  return false;
}
