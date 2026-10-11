import { CategoryView } from "@/components/public/category-view";
import { requireLocale, type SearchParams } from "@/lib/public-api";

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
