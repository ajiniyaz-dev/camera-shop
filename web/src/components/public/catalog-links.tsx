import Link from "next/link";

import { focusLight } from "@/components/public/brand-mark";
import { BrandMetaIcon, CategoryMetaIcon } from "@/components/public/catalog-icons";
import { catalogDestinations } from "@/lib/presentation";
import { messages, type PublicLocale } from "@/lib/public-i18n";

export function CatalogLinks({
  locale,
  brand,
  category,
}: {
  locale: PublicLocale;
  brand: { slug: string; name: string } | null;
  category: { slug: string; parent_slug: string | null; name: string } | null;
}) {
  const text = messages[locale];
  const links = catalogDestinations(locale, brand, category);
  if (!links.length) return null;
  return (
    <p className="flex flex-col gap-1.5 text-sm">
      {links.map((link) => (
        <Link
          key={`${link.kind}-${link.href}`}
          href={link.href}
          className={`inline-flex min-w-0 items-start gap-2 underline-offset-4 hover:underline ${focusLight}`}
        >
          {link.kind === "brand" ? <BrandMetaIcon /> : <CategoryMetaIcon />}
          <span className="min-w-0">
            <span className="text-navy/70">{link.kind === "brand" ? text.brand : text.category}: </span>
            <span className="font-medium text-brand">{link.name}</span>
          </span>
        </Link>
      ))}
    </p>
  );
}
