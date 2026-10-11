import { cache } from "react";
import { notFound } from "next/navigation";

import { getInternalApiUrl } from "@/lib/config";
import { isPublicLocale, type PublicLocale } from "@/lib/public-i18n";

export class PublicCatalogError extends Error {
  readonly status: number;

  constructor(status: number) {
    super("catalog request failed");
    this.name = "PublicCatalogError";
    this.status = status;
  }
}

export type PublicPrice = {
  status: "numeric" | "on_request" | "hidden";
  amount: string | null;
  currency: string | null;
};

export type PublicImage = {
  url: string;
  alt: string;
  width: number | null;
  height: number | null;
  is_primary: boolean;
};

export type PublicBrand = {
  slug: string;
  name: string;
  description: string | null;
  translation_fallback: boolean;
  description_fallback: boolean;
  seo_title?: string | null;
  seo_description?: string | null;
};

export type PublicCategoryRef = {
  slug: string;
  parent_slug: string | null;
  name: string;
  description: string | null;
  translation_fallback: boolean;
  description_fallback: boolean;
  breadcrumb: Array<{ slug: string; parent_slug: string | null; name: string }>;
};

export type PublicCard = {
  slug: string;
  model_display: string;
  option_label: string | null;
  name: string;
  translation_fallback: boolean;
  brand: { slug: string; name: string } | null;
  category: { slug: string; parent_slug: string | null; name: string } | null;
  price: PublicPrice;
  out_of_stock: boolean;
  image: PublicImage | null;
};

export type PublicDetail = PublicCard & {
  description: string | null;
  description_fallback: boolean;
  seo_title: string | null;
  seo_description: string | null;
  specifications: Array<{ name: string; value: string; translation_fallback: boolean }>;
  images: PublicImage[];
  category: PublicCategoryRef | null;
  brand: PublicBrand | null;
};

export type CategoryDetail = {
  slug: string;
  parent_slug: string | null;
  name: string;
  description: string | null;
  translation_fallback: boolean;
  description_fallback: boolean;
  seo_title: string | null;
  seo_description: string | null;
  product_count: number;
  breadcrumb: Array<{ slug: string; parent_slug: string | null; name: string }>;
  children: Array<{ slug: string; parent_slug: string; name: string; product_count: number }>;
};

export type CategoryNode = {
  slug: string;
  name: string;
  description: string | null;
  translation_fallback: boolean;
  product_count: number;
  children: CategoryNode[];
};

export type Company = {
  name: string;
  phone?: string;
  email?: string;
  address?: string;
  opening_hours?: string;
  logo_url?: string;
  social_links?: Array<{ label: string; url: string }>;
};

export type ProductList = {
  locale: string;
  page: number;
  page_size: number;
  total: number;
  sort: string;
  products: PublicCard[];
  brands: Array<{ slug: string; name: string }>;
  categories: Array<{ slug: string; parent_slug: string | null; name: string }>;
};

export type SearchParams = Record<string, string | string[] | undefined>;

export async function publicGet<T>(path: string): Promise<T> {
  const response = await fetch(`${getInternalApiUrl()}${path}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new PublicCatalogError(response.status);
  }
  return (await response.json()) as T;
}

export const loadPublic = cache(publicGet) as typeof publicGet;

export async function publicGetOrNotFound<T>(path: string): Promise<T> {
  try {
    return await loadPublic<T>(path);
  } catch (error) {
    if (error instanceof PublicCatalogError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}

export async function requireLocale(params: Promise<{ locale: string }>): Promise<PublicLocale> {
  const { locale } = await params;
  if (!isPublicLocale(locale)) {
    notFound();
  }
  return locale;
}

export function categoryApiPath(locale: string, slug: string, parent?: string): string {
  if (parent) {
    return `/api/public/categories/${encodeURIComponent(parent)}/${encodeURIComponent(slug)}?locale=${locale}`;
  }
  return `/api/public/categories/${encodeURIComponent(slug)}?locale=${locale}`;
}

export function categoryPath(locale: string, slug: string, parentSlug: string | null): string {
  if (parentSlug) {
    return `/${locale}/categories/${parentSlug}/${slug}`;
  }
  return `/${locale}/categories/${slug}`;
}
