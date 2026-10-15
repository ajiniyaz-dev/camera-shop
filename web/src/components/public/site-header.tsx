import Link from "next/link";
import { Suspense } from "react";

import { AccentBar, BrandMark, focusDark } from "@/components/public/brand-mark";
import { LanguageSwitcher } from "@/components/public/language-switcher";
import { SiteNav } from "@/components/public/site-nav";
import type { Company } from "@/lib/public-api";
import { PUBLIC_LOCALES, messages, type PublicLocale } from "@/lib/public-i18n";

export function SiteHeader({ locale, company }: { locale: PublicLocale; company: Company }) {
  const text = messages[locale];
  const links = [
    { href: `/${locale}`, label: text.home },
    { href: `/${locale}/catalog`, label: text.catalog },
    { href: `/${locale}/categories`, label: text.categories },
    { href: `/${locale}/contact`, label: text.contact },
  ];
  return (
    <header className="bg-navy text-white">
      <a
        href="#content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-10 focus:bg-white focus:px-3 focus:py-2 focus:text-navy focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-brand"
      >
        {text.skip}
      </a>
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
        <Link href={`/${locale}`} className={`inline-flex min-h-11 items-center gap-3 ${focusDark}`}>
          <BrandMark />
          <span className="text-base font-semibold tracking-wide">{company.name}</span>
        </Link>
        <div className="hidden min-w-0 flex-1 md:block">
          <SiteNav links={links} label={text.menu} />
        </div>
        <div className="ml-auto md:ml-0">
          <Suspense
            fallback={
              <nav aria-label={text.language} className="flex flex-wrap gap-1 text-sm">
                {PUBLIC_LOCALES.map((item) => (
                  <a
                    key={item}
                    href={`/${item}`}
                    hrefLang={item}
                    lang={item}
                    className={`inline-flex min-h-11 items-center px-3 text-white ${focusDark}`}
                  >
                    {item === "ru" ? "Русский" : item === "uz" ? "Oʻzbekcha" : "English"}
                  </a>
                ))}
              </nav>
            }
          >
            <LanguageSwitcher locale={locale} />
          </Suspense>
        </div>
      </div>
      <div className="mx-auto max-w-6xl px-4 pb-2 md:hidden">
        <details className="border-t border-white/10 [&:not([open])>:not(summary)]:hidden">
          <summary
            className={`flex min-h-11 cursor-pointer list-none items-center gap-3 text-sm text-white [&::-webkit-details-marker]:hidden ${focusDark}`}
          >
            <span aria-hidden="true" className="h-px w-4 bg-teal" />
            {text.menu}
          </summary>
          <SiteNav links={links} label={text.menu} />
        </details>
      </div>
      <AccentBar />
    </header>
  );
}
