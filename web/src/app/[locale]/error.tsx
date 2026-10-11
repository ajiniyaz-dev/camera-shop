"use client";

import { usePathname } from "next/navigation";

import { isPublicLocale, messages } from "@/lib/public-i18n";

export default function CatalogError({ reset }: { error: Error; reset: () => void }) {
  const requested = usePathname().split("/")[1] ?? "";
  const locale = isPublicLocale(requested) ? requested : "ru";
  const text = messages[locale];
  return (
    <main className="space-y-4 py-8">
      <h1 className="text-2xl font-semibold">{text.error}</h1>
      <p role="alert">{text.error}</p>
      <button
        type="button"
        onClick={reset}
        className="rounded bg-slate-950 px-4 py-2 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-800"
      >
        {text.retry}
      </button>
    </main>
  );
}
