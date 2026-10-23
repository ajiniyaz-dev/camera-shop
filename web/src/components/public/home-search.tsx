"use client";

import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";

import { CameraGlyph, focusLight } from "@/components/public/brand-mark";
import { ProductPhoto } from "@/components/public/product-photo";
import {
  activeTarget,
  loadSuggestions,
  moveActive,
  searchPlan,
  showAllResults,
  suggestionOptionCount,
  SearchGeneration,
  type SuggestionProduct,
} from "@/lib/home-search";
import { formatPublicPrice } from "@/lib/price-format";
import { messages, type PublicLocale } from "@/lib/public-i18n";

type Status = "idle" | "loading" | "ready" | "empty" | "error";

export function HomeSearch({ locale, compact = false }: { locale: PublicLocale; compact?: boolean }) {
  const text = messages[locale];
  const router = useRouter();
  const listId = useId();
  const rootRef = useRef<HTMLFormElement>(null);
  const optionsRef = useRef<HTMLDivElement>(null);
  const generation = useRef(new SearchGeneration());
  const abortRef = useRef<AbortController | null>(null);
  const [query, setQuery] = useState("");
  const [term, setTerm] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<Status>("idle");
  const [suggestions, setSuggestions] = useState<SuggestionProduct[]>([]);
  const [total, setTotal] = useState(0);
  const [active, setActive] = useState(-1);

  const includeAll = showAllResults(status, total);
  const optionCount = suggestionOptionCount(suggestions.length, includeAll);

  useEffect(() => {
    const plan = searchPlan(query);
    if (!plan.term) {
      generation.current.next();
      abortRef.current?.abort();
      abortRef.current = null;
      setTerm(null);
      setOpen(false);
      setStatus("idle");
      setSuggestions([]);
      setTotal(0);
      setActive(-1);
      return;
    }
    const id = generation.current.next();
    const timer = window.setTimeout(() => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setTerm(plan.term);
      setStatus("loading");
      setOpen(true);
      setActive(-1);
      setSuggestions([]);
      void loadSuggestions(locale, plan.term as string, controller.signal)
        .then((result) => {
          if (!generation.current.isCurrent(id)) return;
          setSuggestions(result.products);
          setTotal(result.total);
          setStatus(result.products.length > 0 ? "ready" : "empty");
        })
        .catch((error: unknown) => {
          if (error instanceof DOMException && error.name === "AbortError") return;
          if (!generation.current.isCurrent(id)) return;
          setSuggestions([]);
          setTotal(0);
          setStatus("error");
        });
    }, plan.delay);
    return () => {
      window.clearTimeout(timer);
      abortRef.current?.abort();
    };
  }, [locale, query]);

  useEffect(() => {
    function onPointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, []);

  useEffect(() => {
    if (!open || active < 0) return;
    const list = optionsRef.current;
    const option = document.getElementById(`${listId}-${active}`);
    if (!list || !option || !list.contains(option)) return;
    const listRect = list.getBoundingClientRect();
    const optionRect = option.getBoundingClientRect();
    if (optionRect.top < listRect.top) list.scrollTop -= listRect.top - optionRect.top;
    else if (optionRect.bottom > listRect.bottom) list.scrollTop += optionRect.bottom - listRect.bottom;
  }, [active, listId, open]);

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Escape") {
      setOpen(false);
      setActive(-1);
      return;
    }
    const key = event.key;
    const canOpen = status !== "idle" && term !== null;
    if (!open && canOpen && (key === "ArrowDown" || key === "ArrowUp")) {
      event.preventDefault();
      setOpen(true);
      return;
    }
    if (!open) return;
    if (key === "ArrowDown" || key === "ArrowUp") {
      event.preventDefault();
      setActive((current) => moveActive(current, optionCount, key));
      return;
    }
    if (event.key === "Enter" && active >= 0 && term) {
      const href = activeTarget(active, suggestions, includeAll, locale, term);
      if (!href) return;
      event.preventDefault();
      setOpen(false);
      router.push(href);
    }
  }

  const statusText =
    status === "loading"
      ? text.loading
      : status === "empty"
        ? text.noProducts
        : status === "error"
          ? text.error
          : status === "ready"
            ? `${text.results}: ${total}`
            : "";
  const activeId = active >= 0 ? `${listId}-${active}` : undefined;

  return (
    <form ref={rootRef} action={`/${locale}/search`} method="get" role="search" className={`relative w-full ${compact ? "max-w-none" : "max-w-xl"}`}>
      <label htmlFor="home-search" className={compact ? "sr-only" : "text-sm font-semibold text-white"}>
        {text.searchCatalog}
      </label>
      <div className={`flex gap-2 ${compact ? "" : "mt-2 flex-col sm:flex-row"}`}>
        <div className="relative min-w-0 flex-1">
          <input
            id="home-search"
            name="q"
            type="search"
            role="combobox"
            maxLength={80}
            autoComplete="off"
            aria-autocomplete="list"
            aria-expanded={open}
            aria-controls={listId}
            aria-activedescendant={open ? activeId : undefined}
            placeholder={text.searchPlaceholder}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onFocus={() => {
              if (status !== "idle") setOpen(true);
            }}
            onKeyDown={onKeyDown}
            className={`min-h-11 w-full rounded-full border px-4 text-ink shadow-sm placeholder:text-mute focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 ${compact ? "border-[#d9dce3] bg-[#f7f8fa] focus-visible:outline-brand" : "border-white/20 bg-white focus-visible:outline-sky"}`}
          />
          {open ? (
            <div
              id={listId}
              role="listbox"
              aria-label={text.results}
              className="absolute left-0 right-0 top-full z-30 mt-1 flex max-h-[min(18rem,calc(100dvh-12rem))] flex-col overflow-hidden rounded-xl border border-line bg-white text-ink shadow-lift"
            >
              <div ref={optionsRef} className="min-h-0 overflow-y-auto">
                {status === "loading" ? <p className="px-3 py-3 text-sm text-mute">{text.loading}</p> : null}
                {status === "empty" ? <p className="px-3 py-3 text-sm text-mute">{text.noProducts}</p> : null}
                {status === "error" ? <p className="px-3 py-3 text-sm text-mute">{text.error}</p> : null}
                {suggestions.map((product, index) => {
                  const meta = [product.brand?.name, product.category?.name].filter(Boolean).join(" · ");
                  const price = formatPublicPrice(
                    {
                      status: product.price.status,
                      amount: product.price.amount,
                      currency: product.price.currency ?? (product.price.status === "numeric" ? "UZS" : null),
                    },
                    locale,
                  );
                  return (
                    <a
                      key={product.slug}
                      id={`${listId}-${index}`}
                      role="option"
                      aria-selected={active === index}
                      href={`/${locale}/products/${encodeURIComponent(product.slug)}`}
                      className={`flex min-h-11 items-center gap-3 border-b border-navy/5 px-3 py-2 outline-none hover:bg-mist ${active === index ? "bg-mist" : ""} ${focusLight}`}
                    >
                      {product.image ? (
                        <span className="flex h-11 w-11 shrink-0 items-center justify-center bg-mist">
                          <ProductPhoto src={product.image.url} alt="" width={product.image.width} height={product.image.height} />
                        </span>
                      ) : (
                        <span className="grid h-11 w-11 shrink-0 place-items-center bg-mist text-navy">
                          <CameraGlyph className="h-6 w-6" />
                          <span className="sr-only">{text.noImage}</span>
                        </span>
                      )}
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-medium">{product.name || product.model_display}</span>
                        <span className="block truncate text-xs text-navy/60">
                          {product.model_display}
                          {meta ? ` · ${meta}` : ""}
                        </span>
                      </span>
                      {price ? <span className="shrink-0 text-sm font-semibold">{price}</span> : null}
                    </a>
                  );
                })}
              </div>
              {includeAll && term ? (
                <a
                  id={`${listId}-${suggestions.length}`}
                  role="option"
                  aria-selected={active === suggestions.length}
                  href={`/${locale}/search?q=${encodeURIComponent(term)}`}
                  className={`flex min-h-11 shrink-0 items-center border-t border-navy/10 px-3 text-sm font-medium text-brand outline-none hover:bg-mist ${active === suggestions.length ? "bg-mist" : ""} ${focusLight}`}
                >
                  {text.viewAllResults}
                  {total > suggestions.length ? ` (${total})` : ""}
                </a>
              ) : null}
            </div>
          ) : null}
        </div>
        <button type="submit" aria-label={text.search} className={compact ? "grid h-11 w-11 shrink-0 place-items-center rounded-full text-ink hover:bg-mist focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand" : "btn-on-dark min-w-[6.5rem]"}>
          {compact ? <Search aria-hidden="true" className="h-5 w-5" /> : text.search}
        </button>
      </div>
      <p className="sr-only" role="status" aria-live="polite">
        {open ? statusText : ""}
      </p>
    </form>
  );
}
