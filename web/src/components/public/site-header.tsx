import Link from "next/link";
import { Suspense } from "react";

import { LanguageSwitcher } from "@/components/public/language-switcher";
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
    <header className="bg-slate-950 text-white">
      <a
        href={`#content`}
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-10 focus:rounded focus:bg-white focus:px-3 focus:py-2 focus:text-slate-950"
      >
        {text.skip}
      </a>
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-4">
        <Link
          href={`/${locale}`}
          className="text-lg font-semibold tracking-tight focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
        >
          {company.name}
        </Link>
        <Suspense
          fallback={
            <nav aria-label={text.language} className="flex gap-2 text-sm">
              {PUBLIC_LOCALES.map((item) => (
                <a key={item} href={`/${item}`} hrefLang={item} lang={item} className="rounded px-2 py-1 text-white">
                  {item === "ru" ? "Русский" : item === "uz" ? "Oʻzbekcha" : "English"}
                </a>
              ))}
            </nav>
          }
        >
          <LanguageSwitcher locale={locale} />
        </Suspense>
      </div>
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 pb-4 md:flex-row md:items-center md:justify-between">
        <details className="md:hidden">
          <summary className="cursor-pointer rounded px-2 py-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white">
            {text.menu}
          </summary>
          <NavLinks links={links} label={text.menu} />
        </details>
        <div className="hidden md:block">
          <NavLinks links={links} label={text.menu} />
        </div>
        <SearchForm locale={locale} />
      </div>
    </header>
  );
}

function NavLinks({ links, label }: { links: Array<{ href: string; label: string }>; label: string }) {
  return (
    <nav aria-label={label} className="mt-3 flex flex-col gap-2 md:mt-0 md:flex-row md:gap-4">
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className="rounded px-2 py-1 underline-offset-4 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}

function SearchForm({ locale }: { locale: PublicLocale }) {
  const text = messages[locale];
  return (
    <form action={`/${locale}/search`} method="get" role="search" className="flex gap-2">
      <label className="sr-only" htmlFor={`search-${locale}`}>
        {text.search}
      </label>
      <input
        id={`search-${locale}`}
        name="q"
        type="search"
        maxLength={80}
        placeholder={text.searchPlaceholder}
        className="w-full rounded border border-slate-300 bg-white px-3 py-2 text-slate-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-800 md:w-64"
      />
      <button
        type="submit"
        className="rounded bg-white px-3 py-2 text-slate-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
      >
        {text.search}
      </button>
    </form>
  );
}
