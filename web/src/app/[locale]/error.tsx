"use client";

import { usePathname } from "next/navigation";

import { isPublicLocale, messages } from "@/lib/public-i18n";

export default function CatalogError({ reset }: { error: Error; reset: () => void }) {
  const requested = usePathname().split("/")[1] ?? "";
  const locale = isPublicLocale(requested) ? requested : "ru";
  const text = messages[locale];
  return (
    <main className="space-y-4 py-8">
      <h1 className="text-2xl font-semibold text-ink">{text.error}</h1>
      <p role="alert" className="text-mute">{text.error}</p>
      <button type="button" onClick={reset} className="btn-primary">
        {text.retry}
      </button>
    </main>
  );
}
