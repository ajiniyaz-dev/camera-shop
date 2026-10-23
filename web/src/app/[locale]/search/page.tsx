import type { Metadata } from "next";

import { Breadcrumbs } from "@/components/public/breadcrumbs";
import { PageHeading } from "@/components/public/page-heading";
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
  const text = messages[locale];
  const query = await searchParams;
  return (
    <main className="space-y-5">
      <Breadcrumbs
        label={text.navigation}
        items={[
          { name: text.home, path: `/${locale}` },
          { name: text.search, path: `/${locale}/search` },
        ]}
      />
      <PageHeading title={text.search} description={text.searchCatalog} action={{ href: `/${locale}/catalog`, label: text.catalog }} />
      <ProductListing locale={locale} pathname={`/${locale}/search`} searchParams={query} searchOnly />
    </main>
  );
}
