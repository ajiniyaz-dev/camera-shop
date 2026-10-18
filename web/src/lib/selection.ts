export const SELECTION_KEY = "hikvision-catalog-selection";
export const SELECTION_EVENT = "hikvision-selection-change";
export const SELECTION_LIMIT = 50;

const SLUG = /^[a-z0-9-]+$/i;

export type SelectionAdd = "added" | "present" | "full" | "invalid";

export function normalizeSelection(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  const seen = new Set<string>();
  const slugs: string[] = [];
  for (const item of value) {
    if (typeof item !== "string" || !SLUG.test(item) || item.length > 160 || seen.has(item)) continue;
    seen.add(item);
    slugs.push(item);
    if (slugs.length >= SELECTION_LIMIT) break;
  }
  return slugs;
}

export function addToSelection(current: readonly string[], slug: string): { slugs: string[]; status: SelectionAdd } {
  const slugs = normalizeSelection([...current]);
  if (!SLUG.test(slug) || slug.length > 160) return { slugs, status: "invalid" };
  if (slugs.includes(slug)) return { slugs, status: "present" };
  if (slugs.length >= SELECTION_LIMIT) return { slugs, status: "full" };
  return { slugs: [...slugs, slug], status: "added" };
}

export function removeFromSelection(current: readonly string[], slug: string): string[] {
  return normalizeSelection(current).filter((item) => item !== slug);
}

export function readSelection(): string[] {
  if (typeof window === "undefined") return [];
  try {
    return normalizeSelection(JSON.parse(window.localStorage.getItem(SELECTION_KEY) ?? "[]"));
  } catch {
    return [];
  }
}

export function writeSelection(slugs: readonly string[]): string[] {
  const next = normalizeSelection([...slugs]);
  if (typeof window === "undefined") return next;
  window.localStorage.setItem(SELECTION_KEY, JSON.stringify(next));
  window.dispatchEvent(new CustomEvent(SELECTION_EVENT));
  return next;
}

/**
 * Canonical cart page path. Legacy `/{locale}/selection` redirects here.
 * Persisted list storage keys are unchanged.
 */
export function selectionNavHref(locale: string): string {
  return `/${locale}/cart`;
}

/** Accessible label for the header selection control, including an empty count. */
export function selectionNavLabel(selectionWord: string, count: number): string {
  const safe = Number.isFinite(count) && count > 0 ? Math.floor(count) : 0;
  return `${selectionWord}: ${safe}`;
}

/** Visible badge text derived from the current selection length. */
export function selectionBadgeCount(slugs: readonly string[]): number {
  return normalizeSelection([...slugs]).length;
}
