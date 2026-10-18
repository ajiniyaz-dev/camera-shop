import type { PublicDetail } from "./public-api";

export const PRODUCT_SEO_SITE_NAME = "HikVision";

/** Same equipment-code signal as `hasEquipmentModel` in home-featured.ts. */
const MODEL_CODE = /[A-Za-z]{2,}[-/A-Za-z0-9().]*\d/;

function productDisplayName(product: PublicDetail): string {
  const name = product.name.trim();
  return name || product.model_display;
}

/** Include the catalog model only when it is a distinct equipment code, not a translated phrase. */
function distinctModelCode(product: PublicDetail, displayName: string): string | null {
  const model = product.model_display.trim();
  if (!model || model === displayName || !MODEL_CODE.test(model)) {
    return null;
  }
  return model;
}

export function productTitle(product: PublicDetail, siteName = PRODUCT_SEO_SITE_NAME): string {
  if (product.seo_title) {
    return product.seo_title;
  }
  const brand = product.brand?.name ?? siteName;
  const name = productDisplayName(product);
  const model = distinctModelCode(product, name);
  const head = model ? `${name} (${model})` : name;
  return `${head} — ${brand} | ${siteName}`;
}

export function productDescription(product: PublicDetail): string {
  if (product.seo_description) {
    return product.seo_description;
  }
  if (product.description && !product.description_fallback) {
    return product.description;
  }
  const name = productDisplayName(product);
  const parts = [product.brand?.name, name, distinctModelCode(product, name), product.option_label].filter(Boolean);
  const head = parts.join(" ");
  return product.category ? `${head}. ${product.category.name}` : head;
}
