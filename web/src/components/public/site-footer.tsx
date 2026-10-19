import Link from "next/link";

import { AccentBar, BrandMark, focusDark } from "@/components/public/brand-mark";
import type { Company } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

export function SiteFooter({ locale, company }: { locale: PublicLocale; company: Company }) {
  const text = messages[locale];
  const contacts = [
    company.phone ? { label: text.phone, value: company.phone, href: `tel:${company.phone}` } : null,
    company.email ? { label: text.email, value: company.email, href: `mailto:${company.email}` } : null,
    company.address ? { label: text.address, value: company.address, href: undefined } : null,
    company.opening_hours ? { label: text.hours, value: company.opening_hours, href: undefined } : null,
  ].filter((item): item is { label: string; value: string; href: string | undefined } => item !== null);
  const links = [
    { href: `/${locale}`, label: text.home },
    { href: `/${locale}/catalog`, label: text.catalog },
    { href: `/${locale}/categories`, label: text.categories },
    { href: `/${locale}/cart`, label: text.selection },
    { href: `/${locale}/contact`, label: text.contact },
  ];
  return (
    <footer className="mt-12 bg-navy text-white/75">
      <AccentBar />
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:grid-cols-2 sm:gap-10 sm:py-12 lg:grid-cols-3">
        <div className="space-y-3">
          <p className="flex items-center gap-3 text-base font-semibold tracking-wide text-white">
            <BrandMark />
            {company.name}
          </p>
          <p className="max-w-sm text-sm leading-6">{text.heroText}</p>
        </div>
        <nav aria-label={text.navigation} className="flex flex-col items-start gap-1">
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-teal">{text.navigation}</p>
          {links.map((link) => (
            <Link key={link.href} href={link.href} className={`inline-flex min-h-11 items-center text-sm text-white hover:text-teal ${focusDark}`}>
              {link.label}
            </Link>
          ))}
        </nav>
        {contacts.length || company.social_links?.length ? (
          <div className="space-y-3 text-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-teal">{text.contact}</p>
            {contacts.length ? (
              <ul className="space-y-2">
                {contacts.map((item) => (
                  <li key={item.label}>
                    <span className="block text-xs text-white/50">{item.label}</span>
                    {item.href ? (
                      <a className={`text-white hover:text-teal ${focusDark}`} href={item.href}>
                        {item.value}
                      </a>
                    ) : (
                      <span className="text-white">{item.value}</span>
                    )}
                  </li>
                ))}
              </ul>
            ) : null}
            {company.social_links?.length ? (
              <ul className="flex flex-wrap gap-x-4 gap-y-2">
                {company.social_links.map((link) => (
                  <li key={link.url}>
                    <a className={`text-white underline-offset-4 hover:text-teal hover:underline ${focusDark}`} href={link.url}>
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
      </div>
      <div className="border-t border-white/10">
        <p className="mx-auto max-w-6xl px-4 py-4 text-xs text-white/50">{company.name}</p>
      </div>
    </footer>
  );
}
