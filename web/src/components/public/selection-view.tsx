"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { focusLight } from "@/components/public/brand-mark";
import { PriceLabel } from "@/components/public/price-label";
import { formatUzsAmount, selectionTotal } from "@/lib/price-format";
import { billingPeriod, isServicePlan, showOriginalNote } from "@/lib/presentation";
import { messages, type PublicLocale } from "@/lib/public-i18n";
import type { PublicDetail } from "@/lib/public-api";
import { readSelection, removeFromSelection, SELECTION_EVENT, writeSelection } from "@/lib/selection";

type Row =
  | { slug: string; state: "ready"; product: PublicDetail }
  | { slug: string; state: "error" };

export function SelectionView({ locale }: { locale: PublicLocale }) {
  const text = messages[locale];
  const [rows, setRows] = useState<Row[]>([]);
  const [dropped, setDropped] = useState(false);
  const [ready, setReady] = useState(false);
  const loading = useRef(false);

  useEffect(() => {
    let active = true;
    async function load() {
      if (loading.current) return;
      loading.current = true;
      const slugs = readSelection();
      if (!slugs.length) {
        if (active) {
          setRows([]);
          setDropped(false);
          setReady(true);
        }
        loading.current = false;
        return;
      }
      const loaded = await Promise.all(slugs.map((slug) => loadProduct(locale, slug)));
      if (!active) {
        loading.current = false;
        return;
      }
      const missing = loaded.filter((item) => item.state === "missing").map((item) => item.slug);
      const kept = loaded.filter((item): item is Row => item.state !== "missing");
      if (missing.length) writeSelection(slugs.filter((slug) => !missing.includes(slug)));
      setDropped(missing.length > 0);
      setRows(kept);
      setReady(true);
      loading.current = false;
    }
    void load();
    const refresh = () => void load();
    window.addEventListener(SELECTION_EVENT, refresh);
    window.addEventListener("storage", refresh);
    return () => {
      active = false;
      window.removeEventListener(SELECTION_EVENT, refresh);
      window.removeEventListener("storage", refresh);
    };
  }, [locale]);

  function remove(slug: string) {
    writeSelection(removeFromSelection(readSelection(), slug));
  }

  const readyPrices = rows.filter((row): row is { slug: string; state: "ready"; product: PublicDetail } => row.state === "ready").map((row) => row.product.price);
  const total = selectionTotal(readyPrices);

  if (!ready) return <p className="text-sm text-navy/70">{text.loading}</p>;

  return (
    <div className="space-y-6">
      <p className="max-w-2xl text-sm leading-6 text-navy/70">{text.selectionNote}</p>
      {dropped ? (
        <p role="status" className="text-sm text-navy/70">
          {text.selectionDropped}
        </p>
      ) : null}
      {rows.some((row) => row.state === "error") ? (
        <p role="status" className="text-sm text-navy/70">
          {text.selectionError}
        </p>
      ) : null}
      {rows.length ? (
        <>
          <ul className="space-y-3">
            {rows.map((row) =>
              row.state === "error" ? (
                <li key={row.slug} className="flex flex-col gap-3 rounded-md border border-navy/10 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-sm text-navy/70">{row.slug}</p>
                  <button type="button" onClick={() => remove(row.slug)} className={`inline-flex min-h-11 items-center text-sm font-medium text-brand ${focusLight}`}>
                    {text.removeFromSelection}
                  </button>
                </li>
              ) : (
                <li key={row.slug} className="rounded-md border border-navy/10 bg-white p-4 shadow-sm sm:p-5">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0 space-y-1">
                      {isServicePlan(row.product) ? <p className="text-xs font-semibold uppercase tracking-[0.14em] text-teal">{text.service}</p> : null}
                      <h2 className="text-lg font-semibold leading-snug text-navy">
                        <Link href={`/${locale}/products/${row.product.slug}`} className={`underline-offset-4 hover:text-brand hover:underline ${focusLight}`}>
                          {row.product.name}
                        </Link>
                      </h2>
                      {showOriginalNote(row.product.translation_fallback, row.product.name) ? (
                        <p className="text-sm text-navy/60">{text.fallback}</p>
                      ) : null}
                      <p className="text-sm text-navy/70">
                        {text.model}: {row.product.model_display}
                      </p>
                      <BillingLine option={row.product.option_label} locale={locale} />
                      <PriceLabel price={row.product.price} locale={locale} />
                    </div>
                    <button type="button" onClick={() => remove(row.slug)} className={`inline-flex min-h-11 shrink-0 items-center justify-center border border-navy/20 px-4 text-sm font-medium text-navy hover:border-brand ${focusLight}`}>
                      {text.removeFromSelection}
                    </button>
                  </div>
                </li>
              ),
            )}
          </ul>
          {total.total ? (
            <div className="rounded-md border border-navy/10 bg-white px-5 py-4 shadow-sm">
              <p className="text-lg font-semibold text-navy">
                {text.selectionTotal}: {formatUzsAmount(total.total, locale)}
              </p>
              {total.excluded ? <p className="mt-2 text-sm text-navy/70">{text.selectionTotalExcludes}</p> : null}
            </div>
          ) : total.excluded ? (
            <p role="status" className="text-sm text-navy/70">
              {text.selectionTotalExcludes}
            </p>
          ) : null}
        </>
      ) : (
        <div role="status" className="rounded-md border border-navy/10 bg-white px-5 py-6 shadow-sm">
          <p className="font-semibold text-navy">{text.selectionEmpty}</p>
          <Link href={`/${locale}/catalog`} className={`mt-4 inline-flex min-h-11 items-center text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>
            {text.browseCatalog}
          </Link>
        </div>
      )}
    </div>
  );
}

function BillingLine({ option, locale }: { option: string | null; locale: PublicLocale }) {
  const text = messages[locale];
  const period = billingPeriod(option);
  if (period) {
    return (
      <p className="text-sm text-navy/80">
        {text.billing}: {period === "monthly" ? text.billingMonthly : text.billingYearly}
      </p>
    );
  }
  if (!option) return null;
  return <p className="text-sm text-navy/70">{option}</p>;
}

async function loadProduct(
  locale: PublicLocale,
  slug: string,
): Promise<Row | { slug: string; state: "missing" }> {
  try {
    const response = await fetch(`/api/public/products/${encodeURIComponent(slug)}?locale=${encodeURIComponent(locale)}`, {
      headers: { Accept: "application/json" },
    });
    if (response.status === 404) return { slug, state: "missing" };
    if (!response.ok) return { slug, state: "error" };
    return { slug, state: "ready", product: (await response.json()) as PublicDetail };
  } catch {
    return { slug, state: "error" };
  }
}
