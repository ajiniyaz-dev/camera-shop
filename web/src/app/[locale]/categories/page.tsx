import type { Metadata } from "next";
import Link from "next/link";

import { Breadcrumbs } from "@/components/public/breadcrumbs";
import { focusLight } from "@/components/public/brand-mark";
import { CategoryIndex } from "@/components/public/category-index";
import { PageHeading } from "@/components/public/page-heading";
import { loadPublic, requireLocale, type CategoryNode } from "@/lib/public-api";
import { messages } from "@/lib/public-i18n";
import { pageMetadata, SITE_NAME } from "@/lib/seo";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const locale = await requireLocale(params);
  const text = messages[locale];
  return pageMetadata({
    locale,
    title: `${text.categories} | ${SITE_NAME}`,
    description: `${SITE_NAME}. ${text.categories}`,
    path: `/${locale}/categories`,
    index: true,
  });
}

export default async function CategoriesPage({ params }: { params: Promise<{ locale: string }> }) {
  const locale = await requireLocale(params);
  const text = messages[locale];
  const body = await loadPublic<{ categories: CategoryNode[] }>(`/api/public/categories?locale=${locale}`);
  return (
    <main className="space-y-8">
      <Breadcrumbs
        label={text.navigation}
        items={[
          { name: text.home, path: `/${locale}` },
          { name: text.categories, path: `/${locale}/categories` },
        ]}
      />
      <PageHeading title={text.categories} description={text.categoryIntro} action={{ href: `/${locale}/catalog`, label: text.catalog }} />
      {body.categories.length ? (
        <CategoryIndex nodes={body.categories} locale={locale} />
      ) : (
        <div role="status" className="rounded-md border border-navy/10 bg-white px-5 py-6 shadow-sm">
          <p className="font-semibold text-navy">{text.homeEmptyCategoriesTitle}</p>
          <p className="mt-1 text-sm leading-6 text-navy/70">{text.homeEmptyCategories}</p>
          <Link href={`/${locale}/catalog`} className={`mt-4 inline-flex min-h-11 items-center text-sm font-medium text-brand underline-offset-4 hover:underline ${focusLight}`}>
            {text.browseCatalog}
          </Link>
        </div>
      )}
    </main>
  );
}
