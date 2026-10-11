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
  const text = messages[locale];
  const policy = listingPolicy(await searchParams);
  return pageMetadata({
    locale,
    title: `${text.search} | HikVision`,
    description: catalogCopy(locale).description,
    path: `/${locale}/search${policy.query}`,
    index: false,
  });
}

export default async function SearchPage({
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
      <h1 className="text-3xl font-semibold">{messages[locale].search}</h1>
      <ProductListing locale={locale} pathname={`/${locale}/search`} searchParams={query} searchOnly />
    </main>
  );
}
