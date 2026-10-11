import type { Metadata } from "next";

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
  const query = await searchParams;
  return (
    <main className="space-y-6">
      <h1 className="text-3xl font-semibold">{messages[locale].products}</h1>
      <ProductListing locale={locale} pathname={`/${locale}/products`} searchParams={query} />
    </main>
  );
}
