import type { Metadata } from "next";

import { schemaBrand } from "@/lib/other-brand";
import { productDescription as buildProductDescription, productTitle as buildProductTitle } from "@/lib/product-seo";
import type { Company, PublicDetail, PublicImage, SearchParams } from "@/lib/public-api";
import { messages, PUBLIC_LOCALES, type PublicLocale } from "@/lib/public-i18n";

export const SITE_NAME = "HikVision";

const OG_LOCALE: Record<PublicLocale, string> = {
  ru: "ru_RU",
  uz: "uz_UZ",
  en: "en_US",
};

const LOOPBACK = new Set(["localhost", "127.0.0.1", "::1"]);

/**
 * Configured public origin. Loopback placeholders are omitted so local
 * development does not advertise localhost as the production canonical host.
 */
export function publicOrigin(): string | null {
  const value = process.env.PUBLIC_SITE_URL?.trim();
  if (!value) {
    return null;
  }
  try {
    const url = new URL(value);
    if (url.protocol !== "http:" && url.protocol !== "https:") {
      return null;
    }
    if (LOOPBACK.has(url.hostname)) {
      return null;
    }
    if (url.pathname !== "/" && url.pathname !== "") {
      return null;
    }
    return url.origin;
  } catch {
    return null;
  }
}

export function swapLocale(path: string, locale: PublicLocale): string {
  const [pathname, query] = path.split("?");
  const parts = pathname.split("/");
  if (parts.length < 2) {
    return `/${locale}`;
  }
  parts[1] = locale;
  const next = parts.join("/") || `/${locale}`;
  return query ? `${next}?${query}` : next;
}

export function clip(value: string, max = 180): string {
  const trimmed = value.replace(/\s+/g, " ").trim();
  if (trimmed.length <= max) {
    return trimmed;
  }
  const sliced = trimmed.slice(0, max);
  const space = sliced.lastIndexOf(" ");
  return (space > 80 ? sliced.slice(0, space) : sliced).trim();
}

export function firstParam(params: SearchParams, key: string): string {
  const value = params[key];
  const raw = Array.isArray(value) ? value[0] : value;
  return raw?.trim() ?? "";
}

const LISTING_KEYS = ["q", "brand", "category", "parent", "min_price", "max_price", "sort"] as const;

/**
 * The first page of a clean listing is indexable and canonical to itself.
 * Filtered, sorted, and later pages keep their own URL and use noindex, so a
 * filter is not described as the unfiltered catalog.
 */
export function listingPolicy(params: SearchParams): { index: boolean; query: string } {
  const page = Number(firstParam(params, "page") || "1");
  const query = new URLSearchParams();
  for (const key of LISTING_KEYS) {
    const value = firstParam(params, key);
    if (value) {
      query.set(key, value);
    }
  }
  const filtered = LISTING_KEYS.some((key) => firstParam(params, key));
  const paged = Number.isFinite(page) && page > 1;
  if (paged) {
    query.set("page", String(page));
  }
  const text = query.toString();
  return { index: !filtered && !paged, query: text ? `?${text}` : "" };
}

type PageInput = {
  locale: PublicLocale;
  title: string;
  description: string;
  path: string;
  index: boolean;
  image?: PublicImage | null;
};

export function pageMetadata(page: PageInput): Metadata {
  const origin = publicOrigin();
  const title = clip(page.title, 120);
  const description = clip(page.description);
  const languages: Record<string, string> = {};
  for (const locale of PUBLIC_LOCALES) {
    languages[locale] = swapLocale(page.path, locale);
  }
  languages["x-default"] = swapLocale(page.path, "ru");
  const image =
    origin && page.image
      ? {
          url: page.image.url,
          width: page.image.width ?? undefined,
          height: page.image.height ?? undefined,
          alt: page.image.alt,
        }
      : undefined;
  return {
    title: { absolute: title },
    description,
    robots: page.index ? { index: true, follow: true } : { index: false, follow: true },
    ...(origin
      ? {
          alternates: {
            canonical: page.path,
            languages,
          },
        }
      : {}),
    openGraph: {
      title,
      description,
      siteName: SITE_NAME,
      locale: OG_LOCALE[page.locale],
      alternateLocale: PUBLIC_LOCALES.filter((locale) => locale !== page.locale).map((locale) => OG_LOCALE[locale]),
      url: origin ? page.path : undefined,
      type: "website",
      images: image ? [image] : undefined,
    },
    twitter: {
      card: image ? "summary_large_image" : "summary",
      title,
      description,
      images: image ? [image.url] : undefined,
    },
  };
}

export function titledPage(locale: PublicLocale, path: string, title: string, description: string, index = true): Metadata {
  return pageMetadata({ locale, title: `${title} | ${SITE_NAME}`, description, path, index });
}

export function productTitle(product: PublicDetail): string {
  return buildProductTitle(product, SITE_NAME);
}

export function productDescription(product: PublicDetail): string {
  return buildProductDescription(product);
}

type NamedSeo = {
  name: string;
  description: string | null;
  description_fallback?: boolean;
  seo_title?: string | null;
  seo_description?: string | null;
};

export function namedTitle(item: NamedSeo): string {
  return item.seo_title || `${item.name} | ${SITE_NAME}`;
}

export function namedDescription(item: NamedSeo): string {
  if (item.seo_description) {
    return item.seo_description;
  }
  if (item.description && !item.description_fallback) {
    return item.description;
  }
  return item.name;
}

export function breadcrumbJson(items: Array<{ name: string; path: string }>): Record<string, unknown> | null {
  const origin = publicOrigin();
  if (!origin || items.length === 0) {
    return null;
  }
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: `${origin}${item.path}`,
    })),
  };
}

export function productJson(product: PublicDetail): Record<string, unknown> {
  const origin = publicOrigin();
  const body: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.name,
    sku: product.slug,
  };
  const manufacturer = schemaBrand(product.brand);
  if (manufacturer) {
    body.brand = manufacturer;
  }
  if (product.category) {
    body.category = product.category.name;
  }
  if (product.description && !product.description_fallback) {
    body.description = product.description;
  }
  if (origin && product.images.length > 0) {
    body.image = product.images.map((image) => `${origin}${image.url}`);
  }
  if (product.price.status === "numeric" && product.price.amount && product.price.currency === "UZS") {
    const offer: Record<string, unknown> = {
      "@type": "Offer",
      price: product.price.amount,
      priceCurrency: "UZS",
    };
    if (product.out_of_stock) {
      offer.availability = "https://schema.org/OutOfStock";
    }
    body.offers = offer;
  }
  return body;
}

export function organizationJson(company: Company): Record<string, unknown> {
  const origin = publicOrigin();
  const body: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": company.address ? "LocalBusiness" : "Organization",
    name: company.name,
  };
  if (origin) {
    body.url = origin;
  }
  if (company.phone) {
    body.telephone = company.phone;
  }
  if (company.email) {
    body.email = company.email;
  }
  if (company.address) {
    body.address = company.address;
  }
  if (origin && company.logo_url) {
    body.logo = `${origin}${company.logo_url}`;
  }
  if (company.social_links?.length) {
    body.sameAs = company.social_links.map((link) => link.url);
  }
  return body;
}

export function websiteJson(locale: PublicLocale, name: string): Record<string, unknown> | null {
  const origin = publicOrigin();
  if (!origin) {
    return null;
  }
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name,
    url: `${origin}/${locale}`,
    potentialAction: {
      "@type": "SearchAction",
      target: `${origin}/${locale}/search?q={search_term_string}`,
      "query-input": "required name=search_term_string",
    },
  };
}

export function entityMetadata(
  locale: PublicLocale,
  path: string,
  item: NamedSeo,
  params: SearchParams,
): Metadata {
  const policy = listingPolicy(params);
  return pageMetadata({
    locale,
    title: namedTitle(item),
    description: namedDescription(item),
    path: `${path}${policy.query}`,
    index: policy.index,
  });
}

export function catalogCopy(locale: PublicLocale): { title: string; description: string } {
  const text = messages[locale];
  return {
    title: `${text.catalog} | ${SITE_NAME}`,
    description: `${SITE_NAME}. ${text.catalog}`,
  };
}
