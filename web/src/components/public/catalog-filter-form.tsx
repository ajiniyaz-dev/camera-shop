"use client";

import Link from "next/link";
import type { FormEvent } from "react";

import { focusLight } from "@/components/public/brand-mark";
import { CatalogFilterSection } from "@/components/public/catalog-filter-section";
import { CatalogPriceFields, preventInvalidPriceSubmit } from "@/components/public/catalog-price-fields";
import { categoryValue, listingHref, type CategoryGroup } from "@/lib/catalog-filters";
import type { CatalogPriceIssue } from "@/lib/catalog-price";
import type { ProductList } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

type Locked = {
  category?: string;
  parent?: string;
  brand?: string;
};

export function CatalogFilterForm({
  pathname,
  locale,
  data,
  groups,
  locked,
  q,
  brand,
  selectedCategoryValue,
  minPrice,
  maxPrice,
  sort,
  pageSize,
  linkQuery,
  priceIssue,
  embedded = false,
}: {
  pathname: string;
  locale: PublicLocale;
  data: ProductList;
  groups: CategoryGroup[];
  locked?: Locked;
  q?: string;
  brand?: string;
  selectedCategoryValue: string;
  minPrice?: string;
  maxPrice?: string;
  sort?: string;
  pageSize?: string;
  linkQuery: Record<string, string | undefined>;
  priceIssue?: CatalogPriceIssue | null;
  embedded?: boolean;
}) {
  const text = messages[locale];

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    preventInvalidPriceSubmit(event, { invalid: text.priceInvalid, range: text.priceRangeInvalid });
  }

  return (
    <form
      action={pathname}
      method="get"
      onSubmit={onSubmit}
      className={embedded ? "space-y-1" : "space-y-1 rounded-xl border border-navy/10 bg-mist/80 p-2.5"}
    >
      {q ? <input type="hidden" name="q" value={q} /> : null}
      {sort && sort !== "model" ? <input type="hidden" name="sort" value={sort} /> : null}
      {pageSize ? <input type="hidden" name="page_size" value={pageSize} /> : null}

      {locked?.category || !groups.length ? null : (
        <CatalogFilterSection id={`${embedded ? "mobile" : "desktop"}-category-panel`} title={text.category}>
          <ul className="mt-1 max-h-64 space-y-0.5 overflow-y-auto px-0.5 pb-1 pr-1">
            <li>
              <Link
                href={listingHref(pathname, { ...linkQuery, category: undefined })}
                className={sidebarLinkClass(!selectedCategoryValue)}
              >
                {text.any}
              </Link>
            </li>
            {groups.map((item) => {
              const value = categoryValue(item.slug);
              const current = selectedCategoryValue === value;
              const ancestor = !current && selectedCategoryValue.startsWith(`${item.slug}/`);
              return (
                <li key={item.slug}>
                  <Link
                    href={listingHref(pathname, { ...linkQuery, category: value })}
                    aria-current={current ? "page" : undefined}
                    title={item.name}
                    className={sidebarLinkClass(current, ancestor)}
                  >
                    {item.name}
                  </Link>
                  {item.children.length ? (
                    <ul className="ml-2.5 border-l-2 border-sky/40 pl-1.5">
                      {item.children.map((child) => {
                        const childValue = categoryValue(child.slug, item.slug);
                        const childCurrent = selectedCategoryValue === childValue;
                        return (
                          <li key={child.slug}>
                            <Link
                              href={listingHref(pathname, { ...linkQuery, category: childValue })}
                              aria-current={childCurrent ? "page" : undefined}
                              title={child.name}
                              className={sidebarLinkClass(childCurrent)}
                            >
                              {child.name}
                            </Link>
                          </li>
                        );
                      })}
                    </ul>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </CatalogFilterSection>
      )}

      {locked?.brand || !data.brands.length ? null : (
        <CatalogFilterSection id={`${embedded ? "mobile" : "desktop"}-brand-panel`} title={text.brand}>
          <ul className="mt-1 max-h-48 space-y-0.5 overflow-y-auto px-0.5 pb-1 pr-1">
            <li>
              <Link
                href={listingHref(pathname, { ...linkQuery, brand: undefined })}
                className={sidebarLinkClass(!brand)}
              >
                {text.allBrands}
              </Link>
            </li>
            {data.brands.map((item) => {
              const current = brand === item.slug;
              return (
                <li key={item.slug}>
                  <Link
                    href={listingHref(pathname, { ...linkQuery, brand: item.slug })}
                    aria-current={current ? "page" : undefined}
                    title={item.name}
                    className={sidebarLinkClass(current)}
                  >
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>
        </CatalogFilterSection>
      )}

      <CatalogFilterSection id={`${embedded ? "mobile" : "desktop"}-price-panel`} title={text.price}>
        <div className="px-0.5 pb-1">
          <CatalogPriceFields
            minLabel={text.minPrice}
            maxLabel={text.maxPrice}
            minPrice={minPrice}
            maxPrice={maxPrice}
            invalidMessage={text.priceInvalid}
            rangeMessage={text.priceRangeInvalid}
            initialIssue={priceIssue}
          />
        </div>
      </CatalogFilterSection>

      {selectedCategoryValue && !locked?.category ? <input type="hidden" name="category" value={selectedCategoryValue} /> : null}
      {brand && !locked?.brand ? <input type="hidden" name="brand" value={brand} /> : null}

      <div className="flex flex-col gap-2 border-t border-navy/10 px-0.5 pt-2.5">
        <button type="submit" className="btn-primary btn-compact w-full">
          {text.applyFilters}
        </button>
        <Link
          href={pathname}
          className={`inline-flex min-h-10 items-center justify-center text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}
        >
          {text.reset}
        </Link>
      </div>
    </form>
  );
}

function sidebarLinkClass(active: boolean, ancestor = false): string {
  const base = `flex min-h-9 min-w-0 w-full items-center truncate rounded-md px-2.5 text-left text-sm leading-snug font-normal ${focusLight}`;
  if (active) {
    return `${base} bg-sky/15 font-semibold text-navy shadow-[inset_3px_0_0_0] shadow-teal`;
  }
  if (ancestor) {
    return `${base} bg-sky/10 text-navy hover:bg-sky/15`;
  }
  return `${base} text-ink hover:bg-sky/10 hover:text-navy`;
}
