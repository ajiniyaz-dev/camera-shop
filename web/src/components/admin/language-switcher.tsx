"use client";

import { usePathname } from "next/navigation";

import { LOCALES, translate, type Locale } from "@/lib/i18n";

const labels: Record<Locale, string> = { ru: "RU", uz: "UZ", en: "EN" };

export function LanguageSwitcher({
  locale,
  tone = "light",
}: {
  locale: Locale;
  tone?: "light" | "dark";
}) {
  const next = usePathname() || "/admin";
  const dark = tone === "dark";

  return (
    <form action="/admin/locale" method="post" className="flex items-center gap-1">
      <span className="sr-only">{translate(locale, "language")}</span>
      <input type="hidden" name="next" value={next} />
      {LOCALES.map((item) => {
        const current = item === locale;
        return (
          <button
            key={item}
            type="submit"
            name="locale"
            value={item}
            aria-current={current ? "true" : undefined}
            className={`rounded-lg px-2.5 py-1 text-sm transition-colors motion-reduce:transition-none ${
              current
                ? "bg-brand text-white shadow-sm shadow-brand/40"
                : dark
                  ? "border border-white/25 text-white/85 hover:bg-white/10"
                  : "border border-line text-ink hover:bg-mist"
            }`}
          >
            {labels[item]}
          </button>
        );
      })}
    </form>
  );
}
