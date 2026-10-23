export type CatalogPriceParse = { status: "empty" } | { status: "valid"; value: string } | { status: "invalid" };

export type CatalogPriceIssue = "invalid" | "range";

/** Public prices are whole non-negative soʻm amounts. Empty is allowed. */
export function parseCatalogPrice(raw: string | null | undefined): CatalogPriceParse {
  if (raw == null) return { status: "empty" };
  const trimmed = raw.trim();
  if (!trimmed) return { status: "empty" };
  if (!/^\d{1,20}$/.test(trimmed)) return { status: "invalid" };
  const canonical = trimmed.replace(/^0+(?=\d)/, "");
  return { status: "valid", value: canonical };
}

export function catalogPriceIssue(min: CatalogPriceParse, max: CatalogPriceParse): CatalogPriceIssue | null {
  if (min.status === "invalid" || max.status === "invalid") return "invalid";
  if (min.status === "valid" && max.status === "valid" && BigInt(min.value) > BigInt(max.value)) {
    return "range";
  }
  return null;
}

export function appliedCatalogPrice(parsed: CatalogPriceParse, issue: CatalogPriceIssue | null): string | undefined {
  if (issue === "range") return undefined;
  return parsed.status === "valid" ? parsed.value : undefined;
}
