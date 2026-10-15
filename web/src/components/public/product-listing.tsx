import Link from "next/link";

import { focusLight } from "@/components/public/brand-mark";
import { ProductCard } from "@/components/public/product-card";
import { publicGetOrNotFound, type ProductList, type SearchParams } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

const sorts = ["model", "name", "newest", "price_asc", "price_desc"] as const;
const field =
  "min-h-11 w-full border border-navy/15 bg-white px-3 text-navy focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand";

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
      <form action={pathname} method="get" className="space-y-4 rounded-md border border-navy/10 bg-white p-4 shadow-sm sm:p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="flex min-w-0 flex-1 flex-col gap-1 text-sm font-medium text-navy">
            {text.search}
            <input name="q" type="search" maxLength={80} defaultValue={q ?? ""} className={field} />
          </label>
          <div className="flex gap-3">
            <button type="submit" className={`inline-flex min-h-11 items-center justify-center bg-brand px-5 text-sm font-medium text-white hover:bg-navy ${focusLight}`}>
              {text.show}
            </button>
            <Link href={pathname} className={`inline-flex min-h-11 items-center text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>
              {text.reset}
            </Link>
          </div>
        </div>
        <details className="border-t border-navy/10 pt-3 [&:not([open])>div]:hidden md:[&:not([open])>div]:grid">
          <summary className={`flex min-h-11 cursor-pointer list-none items-center text-sm font-medium text-brand md:hidden [&::-webkit-details-marker]:hidden ${focusLight}`}>
            {text.filters}
          </summary>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {locked?.brand ? null : (
              <label className="flex flex-col gap-1 text-sm font-medium text-navy">
                {text.brand}
                <select name="brand" defaultValue={brand ?? ""} className={field}>
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
              <label className="flex flex-col gap-1 text-sm font-medium text-navy">
                {text.category}
                <select name="category" defaultValue={categoryValue(category, parent)} className={field}>
                  <option value="">{text.any}</option>
                  {data.categories.map((item) => (
                    <option key={categoryValue(item.slug, item.parent_slug ?? undefined)} value={categoryValue(item.slug, item.parent_slug ?? undefined)}>
                      {item.parent_slug ? `— ${item.name}` : item.name}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <label className="flex flex-col gap-1 text-sm font-medium text-navy">
              {text.minPrice}
              <input name="min_price" inputMode="decimal" defaultValue={minPrice ?? ""} className={field} />
            </label>
            <label className="flex flex-col gap-1 text-sm font-medium text-navy">
              {text.maxPrice}
              <input name="max_price" inputMode="decimal" defaultValue={maxPrice ?? ""} className={field} />
            </label>
            <label className="flex flex-col gap-1 text-sm font-medium text-navy">
              {text.sort}
              <select name="sort" defaultValue={sort} className={field}>
                <option value="model">{text.sortModel}</option>
                <option value="name">{text.sortName}</option>
                <option value="newest">{text.sortNewest}</option>
                <option value="price_asc">{text.sortPriceAsc}</option>
                <option value="price_desc">{text.sortPriceDesc}</option>
              </select>
            </label>
          </div>
        </details>
      </form>
      {!locked?.brand && data.brands.length ? (
        <nav aria-label={text.brand}>
          <ul className="flex flex-wrap gap-2">
            {data.brands.map((item) => (
              <li key={item.slug}>
                <Link
                  href={`/${locale}/brands/${item.slug}`}
                  className={`inline-flex min-h-11 items-center border px-3 text-sm ${focusLight} ${
                    brand === item.slug ? "border-brand bg-brand text-white" : "border-navy/15 bg-white text-navy hover:border-brand"
                  }`}
                >
                  {item.name}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      ) : null}
      <ActiveFilters locale={locale} pathname={pathname} query={linkQuery} data={data} />
      {suppress ? (
        <p role="status" className="rounded-md border border-navy/10 bg-white px-5 py-6 text-sm text-navy/70">
          {text.emptySearch}
        </p>
      ) : (
        <>
          <p role="status" aria-live="polite" className="text-sm text-navy/70">
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
            <div role="status" className="rounded-md border border-navy/10 bg-white px-5 py-6 shadow-sm sm:px-6">
              <p className="font-semibold text-navy">{text.noProducts}</p>
              <div className="mt-4 flex flex-wrap gap-4">
                <Link href={pathname} className={`text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>
                  {text.reset}
                </Link>
                <Link href={`/${locale}/categories`} className={`text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>
                  {text.categories}
                </Link>
                <Link href={`/${locale}/catalog`} className={`text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>
                  {text.catalog}
                </Link>
              </div>
            </div>
          )}
          {data.total > data.page_size ? (
            <nav aria-label={text.page} className="flex flex-wrap items-center gap-4">
              {currentPage > 1 ? (
                <Link href={href(pathname, linkQuery, currentPage - 1)} className={`inline-flex min-h-11 items-center text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>
                  {text.previous}
                </Link>
              ) : (
                <span className="inline-flex min-h-11 items-center text-sm text-navy/40">{text.previous}</span>
              )}
              <span className="text-sm text-navy">
                {text.page} {currentPage} / {pageCount}
              </span>
              {currentPage < pageCount ? (
                <Link href={href(pathname, linkQuery, currentPage + 1)} className={`inline-flex min-h-11 items-center text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>
                  {text.next}
                </Link>
              ) : (
                <span className="inline-flex min-h-11 items-center text-sm text-navy/40">{text.next}</span>
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
  data,
}: {
  locale: PublicLocale;
  pathname: string;
  query: Record<string, string | undefined>;
  data: ProductList;
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
        const shown =
          key === "sort"
            ? sortLabels[value] ?? value
            : key === "brand"
              ? data.brands.find((item) => item.slug === value)?.name ?? value
              : key === "category"
                ? data.categories.find((item) => categoryValue(item.slug, item.parent_slug ?? undefined) === value)?.name ?? value
                : value;
        return (
          <li key={key}>
            <Link href={href(pathname, next, 1)} className={`inline-flex min-h-11 items-center border border-brand/30 bg-mist px-3 text-sm text-navy hover:border-brand ${focusLight}`}>
              {labels[key] ?? key}: {shown}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
