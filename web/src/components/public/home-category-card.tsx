import { CategoryOutlineIcon } from "@/components/public/catalog-icons";

/** Category mark for homepage and category grids. Uses Lucide outlines mapped from reliable slugs. */
export function CategoryGlyph({ slug, className = "h-6 w-6" }: { slug: string; className?: string }) {
  return <CategoryOutlineIcon slug={slug} className={className} />;
}
