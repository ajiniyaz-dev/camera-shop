import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { brandMatchesSiteName, productDescription, productTitle } from "./product-seo.ts";
import type { PublicDetail } from "./public-api.ts";

function detail(overrides: Partial<PublicDetail> & Pick<PublicDetail, "name" | "model_display">): PublicDetail {
  return {
    slug: "sample",
    product_kind: "product",
    option_label: null,
    translation_fallback: false,
    brand: null,
    category: null,
    price: { status: "on_request", amount: null, currency: null },
    out_of_stock: false,
    image: null,
    description: null,
    description_fallback: false,
    seo_title: null,
    seo_description: null,
    specifications: [],
    images: [],
    ...overrides,
  };
}

describe("brandMatchesSiteName", () => {
  it("treats missing brand as the site name", () => {
    assert.equal(brandMatchesSiteName(null, "HikVision"), true);
    assert.equal(brandMatchesSiteName("", "HikVision"), true);
  });

  it("matches common Hikvision casings", () => {
    assert.equal(brandMatchesSiteName("HikVision", "HikVision"), true);
    assert.equal(brandMatchesSiteName("Hikvision", "HikVision"), true);
    assert.equal(brandMatchesSiteName("hikvision", "HikVision"), true);
  });

  it("keeps other brands distinct", () => {
    assert.equal(brandMatchesSiteName("EZVIZ", "HikVision"), false);
    assert.equal(brandMatchesSiteName("HiLook", "HikVision"), false);
  });
});

describe("productTitle", () => {
  it("keeps an explicit seo_title override", () => {
    const product = detail({
      name: "Flexible transition",
      model_display: "гибкий переход",
      seo_title: "Custom SEO title",
    });
    assert.equal(productTitle(product), "Custom SEO title");
  });

  it("does not repeat HikVision when the brand is missing", () => {
    const product = detail({
      name: "Flexible transition",
      model_display: "гибкий переход",
      brand: null,
    });
    assert.equal(productTitle(product), "Flexible transition | HikVision");
  });

  it("does not repeat HikVision when the brand casing matches the site name", () => {
    const product = detail({
      name: "DS-1005KI",
      model_display: "DS-1005KI",
      brand: {
        slug: "hikvision",
        name: "Hikvision",
        description: null,
        translation_fallback: false,
        description_fallback: false,
      },
    });
    assert.equal(productTitle(product), "DS-1005KI | HikVision");
  });

  it("keeps a distinct manufacturer before the site suffix", () => {
    const product = detail({
      name: "CS-C6N",
      model_display: "CS-C6N",
      brand: {
        slug: "ezviz",
        name: "EZVIZ",
        description: null,
        translation_fallback: false,
        description_fallback: false,
      },
    });
    assert.equal(productTitle(product), "CS-C6N — EZVIZ | HikVision");
  });

  it("appends a distinct equipment model code when it differs from the name", () => {
    const product = detail({
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
    assert.equal(productTitle(product), "Dome camera (DS-2CD2143) | HikVision");
  });

  it("does not treat a Cyrillic descriptive model as a distinct code", () => {
    const product = detail({
      name: "Flexible transition",
      model_display: "гибкий переход",
      brand: null,
    });
    assert.equal(productTitle(product), "Flexible transition | HikVision");
  });
});

describe("productDescription", () => {
  it("prefers locale description over the template when it is not a Russian fallback", () => {
    const product = detail({
      name: "Flexible transition",
      model_display: "гибкий переход",
      description: "A flexible transition component.",
      description_fallback: false,
    });
    assert.equal(productDescription(product), "A flexible transition component.");
  });

  it("uses the template when only a Russian fallback description exists", () => {
    const product = detail({
      name: "Брелок",
      model_display: "Брелок",
      brand: {
        slug: "andel",
        name: "Andel",
        description: null,
        translation_fallback: false,
        description_fallback: false,
      },
      description: "Магнитный брелок",
      description_fallback: true,
      category: {
        slug: "skud",
        parent_slug: null,
        name: "Access control",
        description: null,
        translation_fallback: false,
        description_fallback: false,
        breadcrumb: [],
      },
    });
    assert.equal(productDescription(product), "Andel Брелок. Access control");
  });
});
