"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

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
    <nav aria-label={text.language} className="flex gap-2 text-sm">
      {PUBLIC_LOCALES.map((item) => {
        const parts = pathname.split("/");
        parts[1] = item;
        const path = parts.join("/") || `/${item}`;
        const href = query ? `${path}?${query}` : path;
        return (
          <Link
            key={item}
            href={href}
            hrefLang={item}
            lang={item}
            aria-current={item === locale ? "page" : undefined}
            className={`rounded px-2 py-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white ${
              item === locale ? "bg-white text-slate-950" : "text-white underline-offset-4 hover:underline"
            }`}
          >
            {labels[item]}
          </Link>
        );
      })}
    </nav>
  );
}
