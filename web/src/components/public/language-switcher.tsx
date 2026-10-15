"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

import { focusDark } from "@/components/public/brand-mark";
import { PUBLIC_LOCALES, messages, type PublicLocale } from "@/lib/public-i18n";

const labels: Record<PublicLocale, string> = {
  ru: "Русский",
  uz: "Oʻzbekcha",
  en: "English",
};

export function LanguageSwitcher({ locale }: { locale: PublicLocale }) {
  const text = messages[locale];
  const pathname = usePathname() || `/${locale}`;
  const params = useSearchParams();
  const query = params.toString();
  return (
    <nav aria-label={text.language} className="flex flex-wrap items-center gap-1 text-sm">
      {PUBLIC_LOCALES.map((item) => {
        const parts = pathname.split("/");
        parts[1] = item;
        const path = parts.join("/") || `/${item}`;
        const href = query ? `${path}?${query}` : path;
        const current = item === locale;
        return (
          <Link
            key={item}
            href={href}
            hrefLang={item}
            lang={item}
            aria-current={current ? "page" : undefined}
            className={`inline-flex min-h-11 items-center justify-center px-3 ${focusDark} ${
              current ? "bg-brand text-white" : "text-white/80 hover:bg-white/10 hover:text-white"
            }`}
          >
            {labels[item]}
          </Link>
        );
      })}
    </nav>
  );
}
