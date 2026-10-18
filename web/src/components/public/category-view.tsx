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
    <main className="space-y-8">
      <JsonLd data={breadcrumbJson(crumbs)} />
      <Breadcrumbs label={text.categories} items={crumbs} />
      <PageHeading
        title={category.name}
        description={category.description}
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
          <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {category.children.map((child) => (
              <li key={child.slug}>
                <Link
                  href={`/${locale}/categories/${category.slug}/${child.slug}`}
                  className={`flex h-full items-center gap-3 border border-navy/10 bg-white p-4 shadow-sm hover:border-brand ${focusLight}`}
                >
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-mist text-brand">
                    <CategoryOutlineIcon slug={child.slug} className="h-5 w-5" />
                  </span>
                  <span className="min-w-0 font-semibold text-navy">{child.name}</span>
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
