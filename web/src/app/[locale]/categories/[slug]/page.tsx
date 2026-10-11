import { CategoryView } from "@/components/public/category-view";
import { requireLocale, type SearchParams } from "@/lib/public-api";

export default async function CategoryPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string; slug: string }>;
  searchParams: Promise<SearchParams>;
}) {
  const { slug } = await params;
  const locale = await requireLocale(params);
  return <CategoryView locale={locale} slug={slug} searchParams={await searchParams} />;
}
