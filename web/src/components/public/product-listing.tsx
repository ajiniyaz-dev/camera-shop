import Link from "next/link";

import { ProductCard } from "@/components/public/product-card";
import { publicGetOrNotFound, type ProductList, type SearchParams } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

const sorts = ["model", "name", "newest", "price_asc", "price_desc"] as const;

type Locked = {
  category?: string;
  parent?: string;
  brand?: string;
};

function one(params: SearchParams, key: string): string | undefined {
  const value = params[key];
  const text = Array.isArray(value) ? value[0] : value;
  const trimmed = text?.trim();
  return trimmed ? trimmed : undefined;
}

function categoryValue(category?: string, parent?: string): string {
  if (!category) return "";
  return parent ? `${parent}/${category}` : category;
}

export async function ProductListing({
  locale,
  pathname,
  searchParams,
  locked,
  searchOnly = false,
}: {
  locale: PublicLocale;
  pathname: string;
  searchParams: SearchParams;
  locked?: Locked;
  searchOnly?: boolean;
}) {
  const text = messages[locale];
  const requestedSort = one(searchParams, "sort");
  const sort = sorts.includes(requestedSort as (typeof sorts)[number]) ? requestedSort : "model";
  const page = one(searchParams, "page");
  const q = one(searchParams, "q");
  const minPrice = one(searchParams, "min_price");
  const maxPrice = one(searchParams, "max_price");
  const selectedCategory = one(searchParams, "category");
  const split = selectedCategory?.split("/") ?? [];
  const category = locked?.category ?? (split.length > 1 ? split.slice(1).join("/") : split[0]);
  const parent = locked?.parent ?? (split.length > 1 ? split[0] : undefined);
  const brand = locked?.brand ?? one(searchParams, "brand");
  const suppress = searchOnly && !q;
  const api = new URLSearchParams({ locale, sort: sort ?? "model", page_size: suppress ? "1" : "24" });
  if (!suppress && page) api.set("page", page);
  if (q && !suppress) api.set("q", q);
  if (category) api.set("category", category);
  if (parent) api.set("parent", parent);
  if (brand) api.set("brand", brand);
  if (minPrice) api.set("min_price", minPrice);
  if (maxPrice) api.set("max_price", maxPrice);
  const data = await publicGetOrNotFound<ProductList>(`/api/public/products?${api.toString()}`);
  const linkQuery = {
    q,
    brand: locked?.brand ? undefined : brand,
    category: locked?.category ? undefined : categoryValue(category, parent),
    min_price: minPrice,
    max_price: maxPrice,
    sort: sort === "model" ? undefined : sort,
  };
  const pageCount = Math.max(1, Math.ceil(data.total / data.page_size));
  const currentPage = data.page;
  return (
    <div className="space-y-6">
      <form action={pathname} method="get" className="grid gap-4 rounded-lg border border-slate-200 bg-slate-50 p-4 md:grid-cols-2 lg:grid-cols-3">
        <h2 className="text-base font-semibold md:col-span-2 lg:col-span-3">{text.filters}</h2>
        <label className="flex flex-col gap-1 text-sm">
          {text.search}
          <input
            name="q"
            type="search"
            maxLength={80}
            defaultValue={q ?? ""}
            className="rounded border border-slate-300 bg-white px-3 py-2"
          />
        </label>
        {locked?.brand ? null : (
          <label className="flex flex-col gap-1 text-sm">
            {text.brand}
            <select name="brand" defaultValue={brand ?? ""} className="rounded border border-slate-300 bg-white px-3 py-2">
              <option value="">{text.any}</option>
              {data.brands.map((item) => (
                <option key={item.slug} value={item.slug}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
        )}
        {locked?.category ? null : (
          <label className="flex flex-col gap-1 text-sm">
            {text.category}
            <select
              name="category"
              defaultValue={categoryValue(category, parent)}
              className="rounded border border-slate-300 bg-white px-3 py-2"
            >
              <option value="">{text.any}</option>
              {data.categories.map((item) => (
                <option key={categoryValue(item.slug, item.parent_slug ?? undefined)} value={categoryValue(item.slug, item.parent_slug ?? undefined)}>
                  {item.parent_slug ? `— ${item.name}` : item.name}
                </option>
              ))}
            </select>
          </label>
        )}
        <label className="flex flex-col gap-1 text-sm">
          {text.minPrice}
          <input
            name="min_price"
            inputMode="decimal"
            defaultValue={minPrice ?? ""}
            className="rounded border border-slate-300 bg-white px-3 py-2"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          {text.maxPrice}
          <input
            name="max_price"
            inputMode="decimal"
            defaultValue={maxPrice ?? ""}
            className="rounded border border-slate-300 bg-white px-3 py-2"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          {text.sort}
          <select name="sort" defaultValue={sort} className="rounded border border-slate-300 bg-white px-3 py-2">
            <option value="model">{text.sortModel}</option>
            <option value="name">{text.sortName}</option>
            <option value="newest">{text.sortNewest}</option>
            <option value="price_asc">{text.sortPriceAsc}</option>
            <option value="price_desc">{text.sortPriceDesc}</option>
          </select>
        </label>
        <div className="flex items-end gap-3">
          <button type="submit" className="rounded bg-slate-950 px-4 py-2 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-800">
            {text.show}
          </button>
          <Link href={pathname} className="rounded px-2 py-2 underline underline-offset-4">
            {text.reset}
          </Link>
        </div>
      </form>
      <ActiveFilters locale={locale} pathname={pathname} query={linkQuery} />
      {suppress ? (
        <p role="status">{text.emptySearch}</p>
      ) : (
        <>
          <p role="status" aria-live="polite">
            {text.results}: {data.total}
          </p>
          {data.products.length ? (
            <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {data.products.map((product) => (
                <li key={product.slug}>
                  <ProductCard product={product} locale={locale} />
                </li>
              ))}
            </ul>
          ) : (
            <p role="status">{text.noProducts}</p>
          )}
          {data.total > data.page_size ? (
            <nav aria-label={text.page} className="flex items-center gap-4">
              {currentPage > 1 ? (
                <Link href={href(pathname, linkQuery, currentPage - 1)} className="underline underline-offset-4">
                  {text.previous}
                </Link>
              ) : (
                <span className="text-slate-500">{text.previous}</span>
              )}
              <span>
                {text.page} {currentPage} / {pageCount}
              </span>
              {currentPage < pageCount ? (
                <Link href={href(pathname, linkQuery, currentPage + 1)} className="underline underline-offset-4">
                  {text.next}
                </Link>
              ) : (
                <span className="text-slate-500">{text.next}</span>
              )}
            </nav>
          ) : null}
        </>
      )}
    </div>
  );
}

function href(pathname: string, query: Record<string, string | undefined>, page: number): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value) params.set(key, value);
  }
  if (page > 1) params.set("page", String(page));
  const text = params.toString();
  return text ? `${pathname}?${text}` : pathname;
}

function ActiveFilters({
  locale,
  pathname,
  query,
}: {
  locale: PublicLocale;
  pathname: string;
  query: Record<string, string | undefined>;
}) {
  const text = messages[locale];
  const labels: Record<string, string> = {
    q: text.search,
    brand: text.brand,
    category: text.category,
    min_price: text.minPrice,
    max_price: text.maxPrice,
    sort: text.sort,
  };
  const sortLabels: Record<string, string> = {
    model: text.sortModel,
    name: text.sortName,
    newest: text.sortNewest,
    price_asc: text.sortPriceAsc,
    price_desc: text.sortPriceDesc,
  };
  const active = Object.entries(query).filter((entry): entry is [string, string] => Boolean(entry[1]));
  if (!active.length) return null;
  return (
    <ul className="flex flex-wrap gap-2" aria-label={text.filters}>
      {active.map(([key, value]) => {
        const next = { ...query, [key]: undefined };
        return (
          <li key={key}>
            <Link href={href(pathname, next, 1)} className="inline-flex rounded-full border border-slate-300 px-3 py-1 text-sm">
              {labels[key] ?? key}: {key === "sort" ? sortLabels[value] ?? value : value}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
