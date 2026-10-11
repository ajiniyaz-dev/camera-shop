import type { Metadata } from "next";

import { ProductListing } from "@/components/public/product-listing";
import { requireLocale, type SearchParams } from "@/lib/public-api";
import { messages } from "@/lib/public-i18n";
import { catalogCopy, listingPolicy, pageMetadata } from "@/lib/seo";

export async function generateMetadata({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<SearchParams>;
}): Promise<Metadata> {
  const locale = await requireLocale(params);
  const policy = listingPolicy(await searchParams);
  const copy = catalogCopy(locale);
  return pageMetadata({
    locale,
    title: copy.title,
    description: copy.description,
    path: `/${locale}/catalog${policy.query}`,
    index: policy.index,
  });
}

export default async function CatalogPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<SearchParams>;
}) {
  const locale = await requireLocale(params);
  const query = await searchParams;
  return (
    <main className="space-y-6">
      <h1 className="text-3xl font-semibold">{messages[locale].catalog}</h1>
      <ProductListing locale={locale} pathname={`/${locale}/catalog`} searchParams={query} />
    </main>
  );
}
