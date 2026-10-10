"use client";

import { usePathname } from "next/navigation";

import { LOCALES, translate, type Locale } from "@/lib/i18n";

const labels: Record<Locale, string> = { ru: "RU", uz: "UZ", en: "EN" };

export function LanguageSwitcher({ locale }: { locale: Locale }) {
  const next = usePathname() || "/admin";

  return (
    <form action="/admin/locale" method="post" className="flex items-center gap-1">
      <span className="sr-only">{translate(locale, "language")}</span>
      <input type="hidden" name="next" value={next} />
      {LOCALES.map((item) => (
        <button
          key={item}
          type="submit"
          name="locale"
          value={item}
          aria-current={item === locale ? "true" : undefined}
          className={`rounded px-2 py-1 text-sm ${item === locale ? "bg-neutral-900 text-white" : "border border-neutral-300"}`}
        >
          {labels[item]}
        </button>
      ))}
    </form>
  );
}
