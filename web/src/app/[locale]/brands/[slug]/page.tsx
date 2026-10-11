import Link from "next/link";

import { ProductListing } from "@/components/public/product-listing";
import { publicGetOrNotFound, requireLocale, type PublicBrand, type SearchParams } from "@/lib/public-api";
import { messages } from "@/lib/public-i18n";

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
  const brand = await publicGetOrNotFound<PublicBrand>(
    `/api/public/brands/${encodeURIComponent(slug)}?locale=${locale}`,
  );
  return (
    <main className="space-y-8">
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
