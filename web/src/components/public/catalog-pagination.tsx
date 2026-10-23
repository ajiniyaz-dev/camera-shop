"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { focusLight } from "@/components/public/brand-mark";
import { listingHref, pageWindow, parsePageInput } from "@/lib/catalog-filters";
import { messages, type PublicLocale } from "@/lib/public-i18n";

const control =
  "inline-flex min-h-10 min-w-10 items-center justify-center rounded-md border px-2.5 text-sm transition";
const field =
  "min-h-10 w-16 rounded-md border border-line bg-white px-2 text-center text-sm text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand";

export function CatalogPagination({
  pathname,
  query,
  currentPage,
  pageCount,
  text,
}: {
  pathname: string;
  query: Record<string, string | undefined>;
  currentPage: number;
  pageCount: number;
  text: (typeof messages)[PublicLocale];
}) {
  const [error, setError] = useState("");
  const errorId = "catalog-page-error";
  const items = pageWindow(currentPage, pageCount);
  const atFirst = currentPage <= 1;
  const atLast = currentPage >= pageCount;

  function onGo(event: FormEvent<HTMLFormElement>) {
    const form = event.currentTarget;
    const input = form.elements.namedItem("page") as HTMLInputElement;
    const parsed = parsePageInput(input.value, pageCount);
    if (parsed.status === "empty" || parsed.status === "invalid") {
      event.preventDefault();
      setError(text.pageInvalid);
      input.setCustomValidity(text.pageInvalid);
      input.reportValidity();
      return;
    }
    input.setCustomValidity("");
    setError("");
    if (parsed.page === 1) {
      event.preventDefault();
      window.location.assign(listingHref(pathname, query, 1));
      return;
    }
    input.value = String(parsed.page);
  }

  return (
    <nav aria-label={text.page} className="space-y-3 border-t border-line pt-3">
      <div className="flex flex-wrap items-center gap-1.5">
        <PageControl href={listingHref(pathname, query, 1)} disabled={atFirst} label={text.pageFirst} />
        <PageControl href={listingHref(pathname, query, currentPage - 1)} disabled={atFirst} label={text.previous} />
        {items.map((item, index) =>
          item === "ellipsis" ? (
            <span key={`e-${index}`} className="px-1 text-sm text-mute" aria-hidden="true">
              …
            </span>
          ) : item === currentPage ? (
            <span
              key={item}
              aria-current="page"
              className={`${control} border-navy bg-navy font-semibold text-white`}
            >
              {item}
            </span>
          ) : (
            <Link
              key={item}
              href={listingHref(pathname, query, item)}
              className={`${control} ${focusLight} border-line bg-white text-ink hover:border-brand hover:text-brand`}
            >
              {item}
            </Link>
          ),
        )}
        <PageControl href={listingHref(pathname, query, currentPage + 1)} disabled={atLast} label={text.next} />
        <PageControl href={listingHref(pathname, query, pageCount)} disabled={atLast} label={text.pageLast} />
      </div>
      <form action={pathname} method="get" onSubmit={onGo} className="flex flex-wrap items-end gap-2">
        {Object.entries(query).map(([key, value]) =>
          value ? <input key={key} type="hidden" name={key} value={value} /> : null,
        )}
        <label className="flex items-center gap-2 text-xs font-medium text-mute">
          {text.goToPage}
          <input
            name="page"
            inputMode="numeric"
            autoComplete="off"
            pattern="[0-9]*"
            defaultValue={String(currentPage)}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? errorId : undefined}
            className={field}
          />
        </label>
        <button type="submit" className="btn-secondary btn-compact">
          {text.go}
        </button>
        {error ? (
          <p id={errorId} role="alert" className="basis-full text-xs leading-5 text-red-800">
            {error}
          </p>
        ) : null}
      </form>
    </nav>
  );
}

function PageControl({ href, disabled, label }: { href: string; disabled: boolean; label: string }) {
  if (disabled) {
    return (
      <span aria-disabled="true" className={`${control} cursor-not-allowed border-line bg-mist text-mute/70`}>
        {label}
      </span>
    );
  }
  return (
    <Link href={href} className={`${control} ${focusLight} border-line bg-white text-ink hover:border-brand hover:text-brand`}>
      {label}
    </Link>
  );
}
