export const SEARCH_DELAY_MS = 250;
export const SUGGESTION_LIMIT = 6;

export type SuggestionPrice = {
  status: string;
  amount: string | null;
  currency?: string | null;
};

export type SuggestionProduct = {
  slug: string;
  name: string;
  model_display: string;
  option_label: string | null;
  brand: { name: string } | null;
  category: { name: string } | null;
  price: SuggestionPrice;
  image: { url: string; alt: string; width?: number | null; height?: number | null } | null;
};

export type SearchPlan = {
  term: string | null;
  delay: number;
};

export function normalizeSearchTerm(value: string): string | null {
  const term = value.trim().slice(0, 80);
  return term.length > 0 ? term : null;
}

export function searchPlan(value: string): SearchPlan {
  const term = normalizeSearchTerm(value);
  if (!term) return { term: null, delay: 0 };
  return { term, delay: SEARCH_DELAY_MS };
}

export function productsSearchPath(locale: string, term: string, limit = SUGGESTION_LIMIT): string {
  const params = new URLSearchParams({
    locale,
    q: term,
    page: "1",
    page_size: String(limit),
    sort: "model",
  });
  return `/api/public/products?${params.toString()}`;
}

export function productPath(locale: string, slug: string): string {
  return `/${locale}/products/${encodeURIComponent(slug)}`;
}

export function allResultsPath(locale: string, term: string): string {
  return `/${locale}/search?q=${encodeURIComponent(term)}`;
}

export function showAllResults(status: string, total: number): boolean {
  return status === "ready" && total > 0;
}

export function suggestionOptionCount(resultCount: number, includeAll: boolean): number {
  return resultCount + (includeAll ? 1 : 0);
}

export function moveActive(active: number, count: number, key: "ArrowUp" | "ArrowDown"): number {
  if (count <= 0) return -1;
  if (key === "ArrowDown") return active >= count - 1 ? 0 : active + 1;
  return active <= 0 ? count - 1 : active - 1;
}

export function activeTarget(
  active: number,
  suggestions: Array<{ slug: string }>,
  includeAll: boolean,
  locale: string,
  term: string,
): string | null {
  if (active < 0 || active >= suggestionOptionCount(suggestions.length, includeAll)) return null;
  if (active < suggestions.length) return productPath(locale, suggestions[active].slug);
  return allResultsPath(locale, term);
}

export class SearchGeneration {
  private current = 0;

  next(): number {
    this.current += 1;
    return this.current;
  }

  isCurrent(id: number): boolean {
    return id === this.current;
  }
}

export async function loadSuggestions(
  locale: string,
  term: string,
  signal: AbortSignal,
  fetchImpl: typeof fetch = fetch,
): Promise<{ products: SuggestionProduct[]; total: number }> {
  const response = await fetchImpl(productsSearchPath(locale, term), {
    signal,
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error("search failed");
  }
  const data = (await response.json()) as { products?: SuggestionProduct[]; total?: number };
  return {
    products: Array.isArray(data.products) ? data.products : [],
    total: typeof data.total === "number" ? data.total : 0,
  };
}
