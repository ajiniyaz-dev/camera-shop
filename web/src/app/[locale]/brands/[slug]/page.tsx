import type { Metadata } from "next";

import { Breadcrumbs } from "@/components/public/breadcrumbs";
import { JsonLd } from "@/components/public/json-ld";
import { PageHeading } from "@/components/public/page-heading";
import { ProductListing } from "@/components/public/product-listing";
import { showOriginalNote } from "@/lib/presentation";
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
      <Breadcrumbs label={text.navigation} items={crumbs} />
      <PageHeading title={brand.name} description={brand.description} action={{ href: `/${locale}/catalog`, label: text.allProducts }} />
      {showOriginalNote(brand.translation_fallback, brand.name) || showOriginalNote(brand.description_fallback, brand.description) ? (
        <p className="-mt-4 text-sm text-navy/60">{text.fallback}</p>
      ) : null}
      <ProductListing
        locale={locale}
        pathname={`/${locale}/brands/${slug}`}
        searchParams={await searchParams}
        locked={{ brand: slug }}
      />
    </main>
  );
}
