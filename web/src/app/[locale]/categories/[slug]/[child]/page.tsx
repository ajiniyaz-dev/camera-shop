import type { Metadata } from "next";

import { CategoryView } from "@/components/public/category-view";
import { categoryApiPath, publicGetOrNotFound, requireLocale, type CategoryDetail, type SearchParams } from "@/lib/public-api";
import { entityMetadata } from "@/lib/seo";

export async function generateMetadata({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string; slug: string; child: string }>;
  searchParams: Promise<SearchParams>;
}): Promise<Metadata> {
  const { slug, child } = await params;
  const locale = await requireLocale(params);
  const category = await publicGetOrNotFound<CategoryDetail>(categoryApiPath(locale, child, slug));
  return entityMetadata(locale, `/${locale}/categories/${slug}/${child}`, category, await searchParams);
}

export default async function NestedCategoryPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string; slug: string; child: string }>;
  searchParams: Promise<SearchParams>;
}) {
  const { slug, child } = await params;
  const locale = await requireLocale(params);
  return <CategoryView locale={locale} slug={child} parent={slug} searchParams={await searchParams} />;
}
