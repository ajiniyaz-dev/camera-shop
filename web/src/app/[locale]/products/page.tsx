import type { Metadata } from "next";

import { Breadcrumbs } from "@/components/public/breadcrumbs";
import { PageHeading } from "@/components/public/page-heading";
import { ProductListing } from "@/components/public/product-listing";
import { requireLocale, type SearchParams } from "@/lib/public-api";
import { messages } from "@/lib/public-i18n";
import { catalogCopy, pageMetadata } from "@/lib/seo";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const locale = await requireLocale(params);
  const copy = catalogCopy(locale);
  return pageMetadata({
    locale,
    title: `${messages[locale].products} | HikVision`,
    description: copy.description,
    path: `/${locale}/catalog`,
    index: false,
  });
}

export default async function ProductsPage({
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
          { name: text.products, path: `/${locale}/products` },
        ]}
      />
      <PageHeading title={text.products} description={text.productIntro} action={{ href: `/${locale}/catalog`, label: text.catalog }} />
      <ProductListing locale={locale} pathname={`/${locale}/products`} searchParams={query} />
    </main>
  );
}
