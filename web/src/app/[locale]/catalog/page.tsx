import type { Metadata } from "next";

import { Breadcrumbs } from "@/components/public/breadcrumbs";
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
  const text = messages[locale];
  const query = await searchParams;
  return (
    <main className="space-y-5">
      <Breadcrumbs
        label={text.navigation}
        items={[
          { name: text.home, path: `/${locale}` },
          { name: text.catalog, path: `/${locale}/catalog` },
        ]}
      />
      <ProductListing
        locale={locale}
        pathname={`/${locale}/catalog`}
        searchParams={query}
        headingTitle={text.catalog}
        intro={{ title: text.catalogInfoTitle, body: text.catalogInfoBody }}
      />
    </main>
  );
}
