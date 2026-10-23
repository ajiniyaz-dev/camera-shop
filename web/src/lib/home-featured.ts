import type { CategoryNode, PublicCard } from "@/lib/public-api";

export const HERO_CATEGORY_SLUG = "ip-kamery";

export const FEATURED_CATEGORY_SLUGS = [
  "ezviz",
  "nvr-2",
  "ptz-2",
  "colorvu",
  "turbo-hd-kamera",
  "poe-kommutatory",
] as const;

export const SHORTCUT_CATEGORY_SLUGS = [
  "ip-kamery",
  "nvr-2",
  "ptz-2",
  "colorvu",
  "ezviz",
  "skud",
  "domofony-2",
  "poe-kommutatory",
] as const;

const MODEL_CODE = /[A-Za-z]{2,}[-/A-Za-z0-9().]*\d/;

export function hasEquipmentModel(model: string): boolean {
  return MODEL_CODE.test(model);
}

export function pickCategoryProduct(products: PublicCard[], usedImages: ReadonlySet<string>): PublicCard | null {
  const withImage = products.filter((product) => product.image && !usedImages.has(product.image.url));
  return withImage.find((product) => hasEquipmentModel(product.model_display)) ?? withImage[0] ?? null;
}

export function selectHomepageProducts(heroGroup: PublicCard[], featuredGroups: PublicCard[][]) {
  const used = new Set<string>();
  const hero = pickCategoryProduct(heroGroup, used);
  if (hero?.image) used.add(hero.image.url);
  const featured: PublicCard[] = [];
  for (const group of featuredGroups) {
    const product = pickCategoryProduct(group, used);
    if (!product?.image) continue;
    used.add(product.image.url);
    featured.push(product);
  }
  return { hero, featured };
}

export function splitCategories(categories: CategoryNode[], shortcutSlugs: readonly string[]) {
  const bySlug = new Map(categories.map((category) => [category.slug, category]));
  const shortcuts = shortcutSlugs.flatMap((slug) => {
    const category = bySlug.get(slug);
    return category ? [category] : [];
  });
  const shortcutSet = new Set(shortcuts.map((category) => category.slug));
  return {
    shortcuts,
    rest: categories.filter((category) => !shortcutSet.has(category.slug)),
  };
}
