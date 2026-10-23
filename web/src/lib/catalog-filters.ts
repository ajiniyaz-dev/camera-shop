export type FlatCategory = {
  slug: string;
  parent_slug: string | null;
  name: string;
};

export type CategoryGroup = FlatCategory & { children: FlatCategory[] };

/** Encode nested categories the same way the listing form and public API already use. */
export function categoryValue(category?: string, parent?: string): string {
  if (!category) return "";
  return parent ? `${parent}/${category}` : category;
}

export function groupCatalogCategories(categories: readonly FlatCategory[]): CategoryGroup[] {
  const children = new Map<string, FlatCategory[]>();
  for (const item of categories) {
    if (!item.parent_slug) continue;
    const list = children.get(item.parent_slug) ?? [];
    list.push(item);
    children.set(item.parent_slug, list);
  }
  return categories
    .filter((item) => !item.parent_slug)
    .map((item) => ({ ...item, children: children.get(item.slug) ?? [] }));
}

export const PAGE_SIZES = [12, 24, 48] as const;

export function listingHref(pathname: string, query: Record<string, string | undefined>, page = 1): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value) params.set(key, value);
  }
  if (page > 1) params.set("page", String(page));
  const text = params.toString();
  return text ? `${pathname}?${text}` : pathname;
}

export function resultRange(page: number, pageSize: number, total: number): { from: number; to: number } | null {
  if (total <= 0 || page < 1 || pageSize < 1) return null;
  const from = (page - 1) * pageSize + 1;
  if (from > total) return null;
  return { from, to: Math.min(page * pageSize, total) };
}

export function parsePageParam(raw: string | undefined): number {
  if (!raw || !/^\d+$/.test(raw)) return 1;
  const page = Number(raw);
  if (!Number.isSafeInteger(page) || page < 1) return 1;
  return page;
}

export function parsePageSize(raw: string | undefined): number {
  if (!raw || !/^\d+$/.test(raw)) return 24;
  const size = Number(raw);
  return (PAGE_SIZES as readonly number[]).includes(size) ? size : 24;
}

export function parsePageInput(
  raw: string,
  pageCount: number,
): { status: "empty" } | { status: "valid"; page: number } | { status: "invalid" } {
  const trimmed = raw.trim();
  if (!trimmed) return { status: "empty" };
  if (!/^\d+$/.test(trimmed)) return { status: "invalid" };
  const page = Number(trimmed);
  if (!Number.isSafeInteger(page) || page < 1) return { status: "invalid" };
  const last = Math.max(1, pageCount);
  return { status: "valid", page: Math.min(page, last) };
}

export function pageWindow(current: number, total: number, radius = 1): Array<number | "ellipsis"> {
  if (total < 1) return [];
  const page = Math.min(Math.max(1, current), total);
  if (total <= 7) return Array.from({ length: total }, (_, index) => index + 1);
  const shown = new Set([1, total, page]);
  for (let offset = 1; offset <= radius; offset += 1) {
    shown.add(page - offset);
    shown.add(page + offset);
  }
  const ordered = [...shown].filter((item) => item >= 1 && item <= total).sort((left, right) => left - right);
  const items: Array<number | "ellipsis"> = [];
  for (const item of ordered) {
    const previous = items[items.length - 1];
    if (typeof previous === "number" && item - previous > 1) items.push("ellipsis");
    items.push(item);
  }
  return items;
}
