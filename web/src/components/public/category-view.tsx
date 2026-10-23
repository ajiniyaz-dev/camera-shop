import Link from "next/link";

import { Breadcrumbs } from "@/components/public/breadcrumbs";
import { focusLight } from "@/components/public/brand-mark";
import { CategoryOutlineIcon } from "@/components/public/catalog-icons";
import { JsonLd } from "@/components/public/json-ld";
import { PageHeading } from "@/components/public/page-heading";
import { ProductListing } from "@/components/public/product-listing";
import { showOriginalNote } from "@/lib/presentation";
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
    <main className="space-y-5">
      <JsonLd data={breadcrumbJson(crumbs)} />
      <Breadcrumbs label={text.categories} items={crumbs} />
      <PageHeading
        title={category.name}
        description={category.description}
        count={category.product_count}
        action={{ href: `/${locale}/catalog`, label: text.allProducts }}
      />
      {showOriginalNote(category.translation_fallback, category.name) || showOriginalNote(category.description_fallback, category.description) ? (
        <p className="-mt-4 text-sm text-navy/60">{text.fallback}</p>
      ) : null}
      {category.children.length ? (
        <section className="space-y-3" aria-labelledby="subcategories-heading">
          <h2 id="subcategories-heading" className="text-xl font-semibold tracking-tight text-navy">
            {text.subcategories}
          </h2>
          <ul className="flex flex-wrap gap-2">
            {category.children.map((child) => (
              <li key={child.slug}>
                <Link
                  href={`/${locale}/categories/${category.slug}/${child.slug}`}
                  className={`inline-flex min-h-9 items-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-medium text-ink hover:border-brand hover:text-brand ${focusLight}`}
                >
                  <CategoryOutlineIcon slug={child.slug} className="h-4 w-4 text-brand" />
                  {child.name}
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
