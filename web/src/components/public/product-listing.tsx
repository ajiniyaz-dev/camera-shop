import Link from "next/link";

import { focusLight } from "@/components/public/brand-mark";
import { CatalogFilterForm } from "@/components/public/catalog-filter-form";
import { CatalogFilterSection } from "@/components/public/catalog-filter-section";
import { CatalogPagination } from "@/components/public/catalog-pagination";
import { CatalogSearchForm } from "@/components/public/catalog-search-form";
import { CatalogSortSelect } from "@/components/public/catalog-sort";
import { ProductCard } from "@/components/public/product-card";
import {
  categoryValue,
  groupCatalogCategories,
  listingHref,
  parsePageParam,
  parsePageSize,
  resultRange,
} from "@/lib/catalog-filters";
import { appliedCatalogPrice, catalogPriceIssue, parseCatalogPrice } from "@/lib/catalog-price";
import { listingHasActiveFilter } from "@/lib/presentation";
import { publicGetOrNotFound, type ProductList, type SearchParams } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

const sorts = ["model", "name", "newest", "price_asc", "price_desc"] as const;
const chip =
  "inline-flex max-w-[14rem] shrink-0 snap-start items-center truncate rounded-lg border px-3 py-2 text-[13px] font-medium leading-none tracking-tight transition";

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

export async function ProductListing({
  locale,
  pathname,
  searchParams,
  locked,
  searchOnly = false,
  headingTitle,
  headingAction,
  intro,
}: {
  locale: PublicLocale;
  pathname: string;
  searchParams: SearchParams;
  locked?: Locked;
  searchOnly?: boolean;
  headingTitle?: string;
  headingAction?: { href: string; label: string };
  intro?: { title: string; body: string };
}) {
  const text = messages[locale];
  const requestedSort = one(searchParams, "sort");
  const sort = sorts.includes(requestedSort as (typeof sorts)[number]) ? requestedSort : "model";
  const requestedPage = parsePageParam(one(searchParams, "page"));
  const pageSize = parsePageSize(one(searchParams, "page_size"));
  const q = one(searchParams, "q");
  const minRaw = one(searchParams, "min_price");
  const maxRaw = one(searchParams, "max_price");
  const minParsed = parseCatalogPrice(minRaw);
  const maxParsed = parseCatalogPrice(maxRaw);
  const priceIssue = catalogPriceIssue(minParsed, maxParsed);
  const minPrice = appliedCatalogPrice(minParsed, priceIssue);
  const maxPrice = appliedCatalogPrice(maxParsed, priceIssue);
  const selectedCategory = one(searchParams, "category");
  const split = selectedCategory?.split("/") ?? [];
  const category = locked?.category ?? (split.length > 1 ? split.slice(1).join("/") : split[0]);
  const parent = locked?.parent ?? (split.length > 1 ? split[0] : undefined);
  const brand = locked?.brand ?? one(searchParams, "brand");
  const suppress = searchOnly && !q;
  const api = new URLSearchParams({
    locale,
    sort: sort ?? "model",
    page_size: suppress ? "1" : String(pageSize),
  });
  if (!suppress && requestedPage > 1) api.set("page", String(requestedPage));
  if (q && !suppress) api.set("q", q);
  if (category) api.set("category", category);
  if (parent) api.set("parent", parent);
  if (brand) api.set("brand", brand);
  if (minPrice) api.set("min_price", minPrice);
  if (maxPrice) api.set("max_price", maxPrice);
  let data = await publicGetOrNotFound<ProductList>(`/api/public/products?${api.toString()}`);
  const pageCount = Math.max(1, Math.ceil(data.total / data.page_size));
  if (!suppress && data.total > 0 && data.page > pageCount) {
    api.set("page", String(pageCount));
    data = await publicGetOrNotFound<ProductList>(`/api/public/products?${api.toString()}`);
  }
  const linkQuery = {
    q,
    brand: locked?.brand ? undefined : brand,
    category: locked?.category ? undefined : categoryValue(category, parent),
    min_price: minPrice,
    max_price: maxPrice,
    sort: sort === "model" ? undefined : sort,
    page_size: pageSize === 24 ? undefined : String(pageSize),
  };
  const currentPage = data.page;
  const range = resultRange(currentPage, data.page_size, data.total);
  const groups = groupCatalogCategories(data.categories);
  const selectedCategoryValue = categoryValue(category, parent);
  const filtered = listingHasActiveFilter({
    q,
    minPrice,
    maxPrice,
    brand,
    category,
    lockedBrand: Boolean(locked?.brand),
    lockedCategory: Boolean(locked?.category),
  });
  const filterProps = {
    pathname,
    locale,
    data,
    groups,
    locked,
    q,
    brand,
    selectedCategoryValue,
    minPrice: minRaw,
    maxPrice: maxRaw,
    sort,
    pageSize: pageSize === 24 ? undefined : String(pageSize),
    linkQuery,
    priceIssue,
  };
  return (
    <div className="space-y-4">
      {headingTitle ? (
        <header className="flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="min-w-0">
            <div aria-hidden="true" className="accent-rail mb-2" />
            <h1 className="text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
              {headingTitle}
              {!suppress ? <span className="ml-2 text-base font-normal text-mute">({data.total})</span> : null}
            </h1>
          </div>
          {headingAction ? (
            <Link
              href={headingAction.href}
              className={`inline-flex min-h-11 shrink-0 items-center text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}
            >
              {headingAction.label}
            </Link>
          ) : null}
        </header>
      ) : null}
      {intro ? (
        <section className="w-full rounded-xl bg-[#F5F7FA] px-5 py-5 sm:px-7 sm:py-6" aria-label={intro.title}>
          <h2 className="text-lg font-semibold tracking-tight text-[#1D4ED8] sm:text-xl">{intro.title}</h2>
          <p className="mt-2 text-base leading-7 text-[#000000]">{intro.body}</p>
        </section>
      ) : null}
      <CatalogSearchForm
        pathname={pathname}
        locale={locale}
        q={q}
        brand={locked?.brand ? undefined : brand}
        category={locked?.category ? undefined : selectedCategoryValue}
        minPrice={minPrice}
        maxPrice={maxPrice}
        sort={sort}
        pageSize={pageSize === 24 ? undefined : String(pageSize)}
      />
      {!locked?.category && groups.length ? (
        <nav aria-label={text.categories} className="-mx-1">
          <ul className="flex gap-2 overflow-x-auto overscroll-x-contain scroll-smooth px-1 pb-2 pt-0.5 [scrollbar-width:thin] snap-x snap-proximity touch-pan-x">
            <li>
              <Link
                href={listingHref(pathname, { ...linkQuery, category: undefined })}
                className={`${chip} ${focusLight} ${selectedCategoryValue ? "border-line bg-white text-ink hover:border-navy/30 hover:bg-mist" : "border-navy bg-navy text-white shadow-sm"}`}
              >
                {text.allProducts}
              </Link>
            </li>
            {groups.map((item) => {
              const value = categoryValue(item.slug);
              const current = selectedCategoryValue === value;
              const ancestor = parent === item.slug && !current;
              return (
                <li key={item.slug} className="shrink-0">
                  <Link
                    href={listingHref(pathname, { ...linkQuery, category: value })}
                    aria-current={current ? "page" : undefined}
                    title={item.name}
                    className={`${chip} ${focusLight} ${
                      current
                        ? "border-navy bg-navy text-white shadow-sm"
                        : ancestor
                          ? "border-navy/25 bg-mist text-navy"
                          : "border-line bg-white text-ink hover:border-navy/30 hover:bg-mist"
                    }`}
                  >
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      ) : null}

      <div className="grid items-start gap-5 lg:grid-cols-[16.5rem_minmax(0,1fr)]">
        <aside className="lg:sticky lg:top-[7.5rem]">
          <div className="rounded-xl border border-navy/10 bg-mist/80 p-2 lg:hidden">
            <CatalogFilterSection
              id="mobile-filters-panel"
              title={text.filters}
              defaultOpen={false}
              extra={
                filtered ? (
                  <span className="text-xs font-normal text-mute">
                    {text.results}: {data.total}
                  </span>
                ) : null
              }
            >
              <div className="px-0.5 pb-1 pt-1">
                <CatalogFilterForm {...filterProps} embedded />
              </div>
            </CatalogFilterSection>
          </div>
          <div className="hidden lg:block">
            <CatalogFilterForm {...filterProps} />
          </div>
        </aside>

        <div className="min-w-0 space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm font-medium text-ink" role="status" aria-live="polite">
              {suppress
                ? text.emptySearch
                : range
                  ? `${text.showing} ${range.from}–${range.to} ${text.ofTotal} ${data.total}`
                  : `${text.results}: ${data.total}`}
            </p>
            <form action={pathname} method="get" className="flex min-w-[12rem] flex-wrap items-center gap-2">
              {q ? <input type="hidden" name="q" value={q} /> : null}
              {brand && !locked?.brand ? <input type="hidden" name="brand" value={brand} /> : null}
              {selectedCategoryValue && !locked?.category ? (
                <input type="hidden" name="category" value={selectedCategoryValue} />
              ) : null}
              {minPrice ? <input type="hidden" name="min_price" value={minPrice} /> : null}
              {maxPrice ? <input type="hidden" name="max_price" value={maxPrice} /> : null}
              <CatalogSortSelect
                label={text.sort}
                defaultValue={sort ?? "model"}
                options={[
                  { value: "model", label: text.sortModel },
                  { value: "name", label: text.sortName },
                  { value: "newest", label: text.sortNewest },
                  { value: "price_asc", label: text.sortPriceAsc },
                  { value: "price_desc", label: text.sortPriceDesc },
                ]}
              />
              <CatalogSortSelect
                label={text.perPage}
                name="page_size"
                defaultValue={String(pageSize)}
                grow={false}
                options={[
                  { value: "12", label: "12" },
                  { value: "24", label: "24" },
                  { value: "48", label: "48" },
                ]}
              />
              <noscript>
                <button type="submit" className="btn-secondary btn-compact">
                  {text.show}
                </button>
              </noscript>
            </form>
          </div>

          <ActiveFilters locale={locale} pathname={pathname} query={linkQuery} data={data} />

          {suppress ? (
            <p role="status" className="rounded-lg border border-line bg-white px-4 py-5 text-sm text-mute">
              {text.emptySearch}
            </p>
          ) : data.products.length ? (
            <ul className="grid grid-cols-1 gap-3 min-[420px]:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {data.products.map((product) => (
                <li key={product.slug} className="min-w-0">
                  <ProductCard product={product} locale={locale} />
                </li>
              ))}
            </ul>
          ) : (
            <div role="status" className="rounded-lg border border-line bg-white px-4 py-5">
              <p className="font-semibold text-ink">{text.noProducts}</p>
              <div className="mt-3 flex flex-wrap gap-4">
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

          {!suppress && data.total > data.page_size ? (
            <CatalogPagination pathname={pathname} query={linkQuery} currentPage={currentPage} pageCount={pageCount} text={text} />
          ) : null}
        </div>
      </div>
    </div>
  );
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
  };
  const active = Object.entries(query).filter(
    (entry): entry is [string, string] => Boolean(entry[1]) && entry[0] !== "sort" && entry[0] !== "page_size",
  );
  if (!active.length) return null;
  return (
    <ul className="flex flex-wrap gap-2" aria-label={text.selectedFilters}>
      {active.map(([key, value]) => {
        const next = { ...query, [key]: undefined };
        const shown =
          key === "brand"
            ? data.brands.find((item) => item.slug === value)?.name ?? value
            : key === "category"
              ? data.categories.find((item) => categoryValue(item.slug, item.parent_slug ?? undefined) === value)?.name ?? value
              : value;
        return (
          <li key={key}>
            <Link
              href={listingHref(pathname, next)}
              className={`inline-flex min-h-9 items-center gap-1.5 rounded-md border border-brand/30 bg-mist px-2.5 text-xs text-ink hover:border-brand ${focusLight}`}
            >
              {labels[key] ?? key}: {shown}
              <span aria-hidden="true" className="text-mute">
                ×
              </span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
