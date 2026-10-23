"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Suspense } from "react";

import { AccentBar, BrandMark, focusLight } from "@/components/public/brand-mark";
import { LanguageSwitcher } from "@/components/public/language-switcher";
import { SelectionLink } from "@/components/public/selection-link";
import { SiteNav } from "@/components/public/site-nav";
import { HomeSearch } from "@/components/public/home-search";
import type { Company } from "@/lib/public-api";
import { PUBLIC_LOCALES, messages, type PublicLocale } from "@/lib/public-i18n";

export function SiteHeader({ locale, company }: { locale: PublicLocale; company: Company }) {
  const pathname = usePathname() || `/${locale}`;
  const isHome = pathname === `/${locale}`;
  const text = messages[locale];
  const links = [
    { href: `/${locale}`, label: text.home },
    { href: `/${locale}/catalog`, label: text.catalog },
    { href: `/${locale}/contact`, label: text.contact },
  ];
  return (
    <header className="sticky top-0 z-50 border-b border-[#e7edf5] bg-white text-ink shadow-sm">
      <a
        href="#content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[60] focus:bg-white focus:px-3 focus:py-2 focus:text-navy focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-brand"
      >
        {text.skip}
      </a>
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-5 gap-y-2 px-4 py-3">
        <div className="flex min-h-11 min-w-0 flex-1 items-center md:flex-none">
          <Link href={`/${locale}`} aria-label={company.name} className={`inline-flex min-h-11 items-center gap-2 ${focusLight}`}>
            <BrandMark />
            <span className="truncate text-base font-bold tracking-wide">{company.name}</span>
          </Link>
        </div>
        <div className="hidden min-w-0 flex-1 justify-center lg:flex">
          <SiteNav links={links} label={text.menu} tone="light" />
        </div>
        {isHome ? <div className="order-last w-full xl:order-none xl:w-56"><HomeSearch locale={locale} compact /></div> : null}
        <div className="ml-auto flex items-center gap-1 md:ml-0">
          <SelectionLink locale={locale} tone="light" />
          <Suspense
            fallback={
              <nav aria-label={text.language} className="flex flex-wrap gap-1 text-sm">
                {PUBLIC_LOCALES.map((item) => (
                  <a
                    key={item}
                    href={`/${item}`}
                    hrefLang={item}
                    lang={item}
                    className={`inline-flex min-h-11 items-center px-2 text-ink ${focusLight}`}
                  >
                    <span className="sm:hidden">{item.toUpperCase()}</span>
                    <span className="hidden sm:inline">{item === "ru" ? "Русский" : item === "uz" ? "Oʻzbekcha" : "English"}</span>
                  </a>
                ))}
              </nav>
            }
          >
            <LanguageSwitcher locale={locale} tone="light" />
          </Suspense>
        </div>
      </div>
      <div className="mx-auto max-w-6xl px-4 pb-2 lg:hidden">
        <details className="border-t border-line [&:not([open])>:not(summary)]:hidden">
          <summary
            className={`flex min-h-11 cursor-pointer list-none items-center gap-3 text-sm text-ink [&::-webkit-details-marker]:hidden ${focusLight}`}
          >
            <span aria-hidden="true" className="h-px w-4 bg-teal" />
            {text.menu}
          </summary>
          <SiteNav links={links} label={text.menu} tone="light" />
        </details>
      </div>
      <AccentBar />
    </header>
  );
}
