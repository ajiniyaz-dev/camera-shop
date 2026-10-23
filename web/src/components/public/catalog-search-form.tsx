"use client";

import { Search } from "lucide-react";
import { useId, type FormEvent } from "react";

import { focusLight } from "@/components/public/brand-mark";
import { listingHref } from "@/lib/catalog-filters";
import { messages, type PublicLocale } from "@/lib/public-i18n";

export function CatalogSearchForm({
  pathname,
  locale,
  q,
  brand,
  category,
  minPrice,
  maxPrice,
  sort,
  pageSize,
}: {
  pathname: string;
  locale: PublicLocale;
  q?: string;
  brand?: string;
  category?: string;
  minPrice?: string;
  maxPrice?: string;
  sort?: string;
  pageSize?: string;
}) {
  const text = messages[locale];
  const fieldId = useId();
  const preserved = {
    brand,
    category,
    min_price: minPrice,
    max_price: maxPrice,
    sort: sort && sort !== "model" ? sort : undefined,
    page_size: pageSize,
  };

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    const form = event.currentTarget;
    const input = form.elements.namedItem("q") as HTMLInputElement | null;
    if (!input) return;
    const trimmed = input.value.trim();
    if (!trimmed) {
      event.preventDefault();
      window.location.assign(listingHref(pathname, preserved));
      return;
    }
    input.value = trimmed;
  }

  return (
    <form action={pathname} method="get" role="search" onSubmit={onSubmit} className="w-full">
      <label htmlFor={fieldId} className="mb-1.5 block text-sm font-semibold text-navy">
        {text.search}
      </label>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-stretch">
        <div className="relative min-w-0 flex-1">
          <Search
            aria-hidden="true"
            className="pointer-events-none absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-navy/50"
            strokeWidth={2}
          />
          <input
            id={fieldId}
            name="q"
            type="search"
            maxLength={80}
            defaultValue={q ?? ""}
            placeholder={text.searchPlaceholder}
            autoComplete="off"
            className={`min-h-12 w-full rounded-xl border border-navy/15 bg-white pl-11 pr-3 text-base text-ink shadow-sm placeholder:text-mute ${focusLight}`}
          />
        </div>
        <button type="submit" className="btn-primary min-h-12 shrink-0 px-5 sm:w-auto">
          {text.search}
        </button>
      </div>
      {Object.entries(preserved).map(([key, value]) =>
        value ? <input key={key} type="hidden" name={key} value={value} /> : null,
      )}
    </form>
  );
}
