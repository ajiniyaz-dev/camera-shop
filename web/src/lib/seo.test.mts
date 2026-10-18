import assert from "node:assert/strict";
import test from "node:test";

import type { PublicDetail } from "./public-api.ts";
import { PRODUCT_SEO_SITE_NAME, productDescription, productTitle } from "./product-seo.ts";

function detail(partial: Partial<PublicDetail> & Pick<PublicDetail, "slug" | "name" | "model_display">): PublicDetail {
  return {
    product_kind: "product",
    option_label: null,
    translation_fallback: false,
    brand: null,
    category: null,
    price: { status: "numeric", amount: "14400", currency: "UZS" },
    out_of_stock: false,
    image: null,
    description: null,
    description_fallback: false,
    seo_title: null,
    seo_description: null,
    specifications: [],
    images: [],
    ...partial,
  } as PublicDetail;
}

test("product 528 titles use the localized name, not the Russian model, in each locale", () => {
  const russian = detail({
    slug: "product-gibkiy-perekhod",
    name: "гибкий переход",
    model_display: "гибкий переход",
  });
  const uzbek = detail({
    slug: "product-gibkiy-perekhod",
    name: "Egiluvchan o\u2018tish",
    model_display: "гибкий переход",
  });
  const english = detail({
    slug: "product-gibkiy-perekhod",
    name: "Flexible transition",
    model_display: "гибкий переход",
  });

  assert.equal(productTitle(russian), `гибкий переход — ${PRODUCT_SEO_SITE_NAME} | ${PRODUCT_SEO_SITE_NAME}`);
  assert.equal(productTitle(uzbek), `Egiluvchan o\u2018tish — ${PRODUCT_SEO_SITE_NAME} | ${PRODUCT_SEO_SITE_NAME}`);
  assert.equal(productTitle(english), `Flexible transition — ${PRODUCT_SEO_SITE_NAME} | ${PRODUCT_SEO_SITE_NAME}`);
  assert.equal(productTitle(english).includes("гибкий"), false);
});

test("a distinct equipment model code stays in the title beside the localized name", () => {
  const product = detail({
    slug: "child-cam",
    name: "Dome camera",
    model_display: "DS-2CD2143",
    brand: {
      slug: "hikvision",
      name: "Hikvision",
      description: null,
      translation_fallback: false,
      description_fallback: false,
    },
  });
  assert.equal(productTitle(product), `Dome camera (DS-2CD2143) — Hikvision | ${PRODUCT_SEO_SITE_NAME}`);
});

test("an explicit seo_title wins over the localized default", () => {
  const product = detail({
    slug: "seo-cam",
    name: "Flexible transition",
    model_display: "гибкий переход",
    seo_title: "Custom SEO title",
  });
  assert.equal(productTitle(product), "Custom SEO title");
});

test("meta description prefers localized copy and keeps a model code when it adds identity", () => {
  const translated = detail({
    slug: "product-gibkiy-perekhod",
    name: "Flexible transition",
    model_display: "гибкий переход",
    description: "A flexible transition component is used to connect equipment components.",
    description_fallback: false,
    category: {
      slug: "drugie-ustroystva",
      parent_slug: null,
      name: "Other devices",
      description: null,
      translation_fallback: false,
      description_fallback: false,
      breadcrumb: [],
    },
  });
  assert.equal(productDescription(translated), translated.description);

  const noCopy = detail({
    slug: "child-cam",
    name: "Dome camera",
    model_display: "DS-2CD2143",
    option_label: "2.8 mm",
    brand: {
      slug: "hikvision",
      name: "Hikvision",
      description: null,
      translation_fallback: false,
      description_fallback: false,
    },
    category: {
      slug: "domes",
      parent_slug: "cameras",
      name: "Domes",
      description: null,
      translation_fallback: false,
      description_fallback: false,
      breadcrumb: [],
    },
  });
  assert.equal(productDescription(noCopy), "Hikvision Dome camera DS-2CD2143 2.8 mm. Domes");

  const descriptive = detail({
    slug: "product-gibkiy-perekhod",
    name: "Flexible transition",
    model_display: "гибкий переход",
    category: {
      slug: "drugie-ustroystva",
      parent_slug: null,
      name: "Other devices",
      description: null,
      translation_fallback: false,
      description_fallback: false,
      breadcrumb: [],
    },
  });
  assert.equal(productDescription(descriptive), "Flexible transition. Other devices");
  assert.equal(productDescription(descriptive).includes("гибкий"), false);
});
