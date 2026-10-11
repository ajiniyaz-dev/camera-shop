import Link from "next/link";

import { JsonLd } from "@/components/public/json-ld";
import { ProductListing } from "@/components/public/product-listing";
import { categoryApiPath, categoryPath, publicGetOrNotFound, type CategoryDetail, type SearchParams } from "@/lib/public-api";
import { messages, type PublicLocale } from "@/lib/public-i18n";
import { breadcrumbJson } from "@/lib/seo";

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
  const category = await publicGetOrNotFound<CategoryDetail>(categoryApiPath(locale, slug, parent));
  const pagePath = parent ? `/${locale}/categories/${parent}/${slug}` : `/${locale}/categories/${slug}`;
  const crumbs = [
    { name: text.home, path: `/${locale}` },
    { name: text.categories, path: `/${locale}/categories` },
    ...category.breadcrumb.map((item) => ({
      name: item.name,
      path: categoryPath(locale, item.slug, item.parent_slug),
    })),
  ];
  return (
    <main className="space-y-8">
      <JsonLd data={breadcrumbJson(crumbs)} />
      <nav aria-label={text.categories}>
        <ol className="flex flex-wrap gap-2 text-sm text-slate-700">
          {crumbs.map((item, index) => (
            <li key={item.path}>
              {index > 0 ? <span aria-hidden="true">/ </span> : null}
              <Link href={item.path} className="underline underline-offset-4">
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
