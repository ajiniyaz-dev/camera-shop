import type { Metadata } from "next";
import Link from "next/link";

import { JsonLd } from "@/components/public/json-ld";
import { ProductListing } from "@/components/public/product-listing";
import { publicGetOrNotFound, requireLocale, type PublicBrand, type SearchParams } from "@/lib/public-api";
import { messages } from "@/lib/public-i18n";
import { breadcrumbJson, entityMetadata } from "@/lib/seo";

export async function generateMetadata({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string; slug: string }>;
  searchParams: Promise<SearchParams>;
}): Promise<Metadata> {
  const { slug } = await params;
  const locale = await requireLocale(params);
  const brand = await publicGetOrNotFound<PublicBrand>(`/api/public/brands/${encodeURIComponent(slug)}?locale=${locale}`);
  return entityMetadata(locale, `/${locale}/brands/${slug}`, brand, await searchParams);
}

export default async function BrandPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string; slug: string }>;
  searchParams: Promise<SearchParams>;
}) {
  const { slug } = await params;
  const locale = await requireLocale(params);
  const text = messages[locale];
  const brand = await publicGetOrNotFound<PublicBrand>(`/api/public/brands/${encodeURIComponent(slug)}?locale=${locale}`);
  const crumbs = [
    { name: text.home, path: `/${locale}` },
    { name: text.catalog, path: `/${locale}/catalog` },
    { name: brand.name, path: `/${locale}/brands/${slug}` },
  ];
  return (
    <main className="space-y-8">
      <JsonLd data={breadcrumbJson(crumbs)} />
      <nav aria-label={text.categories} className="text-sm text-slate-700">
        <ol className="flex flex-wrap gap-2">
          {crumbs.map((item, index) => (
            <li key={item.path}>
              {index > 0 ? <span aria-hidden="true">/ </span> : null}
              {index === crumbs.length - 1 ? (
                <span>{item.name}</span>
              ) : (
                <Link href={item.path} className="underline underline-offset-4">
                  {item.name}
                </Link>
              )}
            </li>
          ))}
        </ol>
      </nav>
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold">{brand.name}</h1>
        {brand.translation_fallback ? <p className="text-sm text-slate-600">{text.fallback}</p> : null}
        {brand.description ? <p className="max-w-3xl leading-7">{brand.description}</p> : null}
        <p>
          <Link href={`/${locale}/catalog`} className="underline underline-offset-4">
            {text.allProducts}
          </Link>
        </p>
      </header>
      <ProductListing
        locale={locale}
        pathname={`/${locale}/brands/${slug}`}
        searchParams={await searchParams}
        locked={{ brand: slug }}
      />
    </main>
  );
}
