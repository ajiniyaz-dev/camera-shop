import Link from "next/link";

import { ProductListing } from "@/components/public/product-listing";
import { publicGetOrNotFound, type SearchParams } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";

type CategoryDetail = {
  slug: string;
  parent_slug: string | null;
  name: string;
  description: string | null;
  translation_fallback: boolean;
  product_count: number;
  breadcrumb: Array<{ slug: string; parent_slug: string | null; name: string }>;
  children: Array<{ slug: string; parent_slug: string; name: string; product_count: number }>;
};

export async function CategoryView({
  locale,
  slug,
  parent,
  searchParams,
}: {
  locale: PublicLocale;
  slug: string;
  parent?: string;
  searchParams: SearchParams;
}) {
  const text = messages[locale];
  const path = parent
    ? `/api/public/categories/${encodeURIComponent(parent)}/${encodeURIComponent(slug)}?locale=${locale}`
    : `/api/public/categories/${encodeURIComponent(slug)}?locale=${locale}`;
  const category = await publicGetOrNotFound<CategoryDetail>(path);
  const pagePath = parent ? `/${locale}/categories/${parent}/${slug}` : `/${locale}/categories/${slug}`;
  return (
    <main className="space-y-8">
      <nav aria-label={text.categories}>
        <ol className="flex flex-wrap gap-2 text-sm text-slate-700">
          <li>
            <Link href={`/${locale}/categories`} className="underline underline-offset-4">
              {text.categories}
            </Link>
          </li>
          {category.breadcrumb.map((item) => (
            <li key={`${item.parent_slug ?? ""}/${item.slug}`}>
              <span aria-hidden="true">/</span>{" "}
              <Link
                href={
                  item.parent_slug
                    ? `/${locale}/categories/${item.parent_slug}/${item.slug}`
                    : `/${locale}/categories/${item.slug}`
                }
                className="underline underline-offset-4"
              >
                {item.name}
              </Link>
            </li>
          ))}
        </ol>
      </nav>
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold">{category.name}</h1>
        {category.translation_fallback ? <p className="text-sm text-slate-600">{text.fallback}</p> : null}
        {category.description ? <p className="max-w-3xl leading-7 text-slate-800">{category.description}</p> : null}
        <p className="text-sm text-slate-600">
          {text.products}: {category.product_count}
        </p>
      </header>
      {category.children.length ? (
        <section className="space-y-3" aria-labelledby="subcategories-heading">
          <h2 id="subcategories-heading" className="text-xl font-semibold">
            {text.subcategories}
          </h2>
          <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {category.children.map((child) => (
              <li key={child.slug} className="rounded border border-slate-200 p-4">
                <Link href={`/${locale}/categories/${category.slug}/${child.slug}`} className="font-medium underline underline-offset-4">
                  {child.name}
                </Link>
                <p className="mt-1 text-sm text-slate-600">
                  {text.products}: {child.product_count}
                </p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      <ProductListing
        locale={locale}
        pathname={pagePath}
        searchParams={searchParams}
        locked={{ category: slug, parent }}
      />
    </main>
  );
}
