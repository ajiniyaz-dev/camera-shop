"use client";

import { usePathname } from "next/navigation";

import { isPublicLocale, messages } from "@/lib/public-i18n";

export default function CatalogError({ reset }: { error: Error; reset: () => void }) {
  const requested = usePathname().split("/")[1] ?? "";
  const locale = isPublicLocale(requested) ? requested : "ru";
  const text = messages[locale];
  return (
    <main className="space-y-4 py-8">
      <h1 className="text-2xl font-semibold text-navy">{text.error}</h1>
      <p role="alert" className="text-navy/70">{text.error}</p>
      <button
        type="button"
        onClick={reset}
        className="inline-flex min-h-11 items-center bg-brand px-5 text-sm font-medium text-white hover:bg-navy focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
      >
        {text.retry}
      </button>
    </main>
  );
}
