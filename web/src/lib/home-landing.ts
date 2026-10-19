/** Verified published category slugs used by homepage landing sections. */
export const LANDING_CATEGORY_SLUGS = {
  colorvu: "colorvu",
  acusenseDvr: "acusense-dvr",
  ipCameras: "ip-kamery",
  nvr: "nvr-2",
  dvr: "dvr",
  hdd: "hdd",
  poe: "poe-kommutatory",
  cables: "kabeli-i-razyomy",
  ezviz: "ezviz",
  accessControl: "skud",
  ptz: "ptz-2",
  project: "proektnoe-oborudovanie",
  turboHd: "turbo-hd-kamera",
} as const;

export type LandingCategorySlug = (typeof LANDING_CATEGORY_SLUGS)[keyof typeof LANDING_CATEGORY_SLUGS];

export type LandingTechId = "colorvu" | "acusense" | "darkfighter" | "hikconnect";
export type LandingSolutionId = "home" | "retail" | "office" | "warehouse";
export type LandingSystemId = "cameras" | "recorder" | "storage" | "network";

export type LandingTechDef = {
  id: LandingTechId;
  /** Category to open when present in the live catalog; omit when no verified section exists. */
  categorySlug?: LandingCategorySlug;
  /** Prefer contact when no dedicated catalog section is verified. */
  preferContact?: boolean;
};

export type LandingSolutionDef = {
  id: LandingSolutionId;
  categorySlugs: readonly LandingCategorySlug[];
};

export type LandingSystemDef = {
  id: LandingSystemId;
  categorySlugs: readonly LandingCategorySlug[];
};

export type LandingCategoryRef = {
  slug: string;
  name: string;
  parentSlug: string | null;
};

export const LANDING_TECHNOLOGIES: readonly LandingTechDef[] = [
  { id: "colorvu", categorySlug: LANDING_CATEGORY_SLUGS.colorvu },
  { id: "acusense", categorySlug: LANDING_CATEGORY_SLUGS.acusenseDvr },
  { id: "darkfighter" },
  { id: "hikconnect", preferContact: true },
];

export const LANDING_SOLUTIONS: readonly LandingSolutionDef[] = [
  {
    id: "home",
    categorySlugs: [LANDING_CATEGORY_SLUGS.colorvu, LANDING_CATEGORY_SLUGS.ezviz, LANDING_CATEGORY_SLUGS.ipCameras],
  },
  {
    id: "retail",
    categorySlugs: [LANDING_CATEGORY_SLUGS.ipCameras, LANDING_CATEGORY_SLUGS.accessControl, LANDING_CATEGORY_SLUGS.nvr],
  },
  {
    id: "office",
    categorySlugs: [LANDING_CATEGORY_SLUGS.ipCameras, LANDING_CATEGORY_SLUGS.nvr, LANDING_CATEGORY_SLUGS.accessControl],
  },
  {
    id: "warehouse",
    categorySlugs: [LANDING_CATEGORY_SLUGS.ptz, LANDING_CATEGORY_SLUGS.nvr, LANDING_CATEGORY_SLUGS.project],
  },
];

export const LANDING_SYSTEM_PARTS: readonly LandingSystemDef[] = [
  { id: "cameras", categorySlugs: [LANDING_CATEGORY_SLUGS.ipCameras, LANDING_CATEGORY_SLUGS.turboHd] },
  { id: "recorder", categorySlugs: [LANDING_CATEGORY_SLUGS.nvr, LANDING_CATEGORY_SLUGS.dvr] },
  { id: "storage", categorySlugs: [LANDING_CATEGORY_SLUGS.hdd] },
  {
    id: "network",
    categorySlugs: [LANDING_CATEGORY_SLUGS.poe, LANDING_CATEGORY_SLUGS.cables],
  },
];

export function availableLandingCategories(categories: readonly LandingCategoryRef[]): Map<string, LandingCategoryRef> {
  return new Map(categories.map((category) => [category.slug, category]));
}

export function categoryHref(
  locale: string,
  slug: string,
  available: ReadonlyMap<string, LandingCategoryRef>,
): string | null {
  const category = available.get(slug);
  if (!category) return null;
  if (category.parentSlug) {
    return `/${locale}/categories/${category.parentSlug}/${category.slug}`;
  }
  return `/${locale}/categories/${category.slug}`;
}

export function firstCategoryHref(
  locale: string,
  slugs: readonly string[],
  available: ReadonlyMap<string, LandingCategoryRef>,
): string | null {
  for (const slug of slugs) {
    const href = categoryHref(locale, slug, available);
    if (href) return href;
  }
  return null;
}

export function techHref(
  tech: LandingTechDef,
  locale: string,
  available: ReadonlyMap<string, LandingCategoryRef>,
): { href: string; kind: "category" | "contact" } | null {
  if (tech.preferContact) {
    return { href: `/${locale}/contact`, kind: "contact" };
  }
  if (!tech.categorySlug) return null;
  const href = categoryHref(locale, tech.categorySlug, available);
  return href ? { href, kind: "category" } : null;
}
