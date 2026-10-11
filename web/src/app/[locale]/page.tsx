import Link from "next/link";

import { ContactDetails } from "@/components/public/contact-details";
import { ProductCard } from "@/components/public/product-card";
import { publicGet, requireLocale, type CategoryNode, type Company, type PublicCard } from "@/lib/public-api";
import { messages } from "@/lib/public-i18n";

type HomePayload = {
  company: Company;
  categories: CategoryNode[];
  products: PublicCard[];
};

export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const locale = await requireLocale(params);
  const text = messages[locale];
  const home = await publicGet<HomePayload>(`/api/public/home?locale=${locale}`);
  return (
    <main className="space-y-12">
      <section className="space-y-4">
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{home.company.name}</h1>
        <form action={`/${locale}/search`} method="get" role="search" className="flex max-w-xl flex-col gap-2 sm:flex-row">
          <label className="sr-only" htmlFor="home-search">
            {text.search}
          </label>
          <input
            id="home-search"
            name="q"
            type="search"
            maxLength={80}
            placeholder={text.searchPlaceholder}
            className="w-full rounded border border-slate-300 px-3 py-2"
          />
          <button type="submit" className="rounded bg-slate-950 px-4 py-2 text-white">
            {text.search}
          </button>
        </form>
      </section>
      <section className="space-y-4" aria-labelledby="categories-heading">
        <h2 id="categories-heading" className="text-2xl font-semibold">
          <Link href={`/${locale}/categories`} className="underline-offset-4 hover:underline">
            {text.categories}
          </Link>
        </h2>
        {home.categories.length ? (
          <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {home.categories.map((category) => (
              <li key={category.slug} className="rounded-lg border border-slate-200 p-4">
                <h3 className="text-lg font-semibold">
                  <Link href={`/${locale}/categories/${category.slug}`} className="underline-offset-4 hover:underline">
                    {category.name}
                  </Link>
                </h3>
                {category.translation_fallback ? <p className="mt-1 text-sm text-slate-600">{text.fallback}</p> : null}
                {category.description ? <p className="mt-2 text-sm leading-6 text-slate-700">{category.description}</p> : null}
                <p className="mt-3 text-sm text-slate-600">
                  {text.products}: {category.product_count}
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <p>{text.noCategories}</p>
        )}
      </section>
      <section className="space-y-4" aria-labelledby="products-heading">
        <div className="flex items-baseline justify-between gap-4">
          <h2 id="products-heading" className="text-2xl font-semibold">
            {text.products}
          </h2>
          <Link href={`/${locale}/catalog`} className="underline underline-offset-4">
            {text.catalog}
          </Link>
        </div>
        {home.products.length ? (
          <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {home.products.map((product) => (
              <li key={product.slug}>
                <ProductCard product={product} locale={locale} />
              </li>
            ))}
          </ul>
        ) : (
          <p>{text.noProducts}</p>
        )}
      </section>
      <ContactDetails company={home.company} locale={locale} />
    </main>
  );
}
