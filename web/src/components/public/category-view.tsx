import Link from "next/link";

import { Breadcrumbs } from "@/components/public/breadcrumbs";
import { focusLight } from "@/components/public/brand-mark";
import { JsonLd } from "@/components/public/json-ld";
import { PageHeading } from "@/components/public/page-heading";
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
      <Breadcrumbs label={text.categories} items={crumbs} />
      <PageHeading
        title={category.name}
        description={category.description}
        action={{ href: `/${locale}/catalog`, label: text.allProducts }}
      />
      {category.translation_fallback ? <p className="-mt-4 text-sm text-navy/60">{text.fallback}</p> : null}
      <p className="text-sm text-navy/70">
        {text.products}: {category.product_count}
      </p>
      {category.children.length ? (
        <section className="space-y-3" aria-labelledby="subcategories-heading">
          <h2 id="subcategories-heading" className="text-xl font-semibold tracking-tight text-navy">
            {text.subcategories}
          </h2>
          <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {category.children.map((child) => (
              <li key={child.slug}>
                <Link
                  href={`/${locale}/categories/${category.slug}/${child.slug}`}
                  className={`flex h-full flex-col border border-navy/10 bg-white p-4 shadow-sm hover:border-brand ${focusLight}`}
                >
                  <span className="font-semibold text-navy">{child.name}</span>
                  <span className="mt-2 text-sm text-navy/70">
                    {text.products}: {child.product_count}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      <ProductListing locale={locale} pathname={pagePath} searchParams={searchParams} locked={{ category: slug, parent }} />
    </main>
  );
}
