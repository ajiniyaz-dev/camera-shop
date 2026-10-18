import assert from "node:assert/strict";
import test from "node:test";

import { pickCategoryProduct, selectHomepageProducts, splitCategories } from "./home-featured.ts";
import type { CategoryNode, PublicCard } from "./public-api.ts";

function card(partial: Partial<PublicCard> & Pick<PublicCard, "slug" | "model_display">): PublicCard {
  return {
    option_label: null,
    name: partial.model_display,
    translation_fallback: false,
    brand: { slug: "hikvision", name: "Hikvision" },
    category: { slug: "ip-kamery", parent_slug: null, name: "IP" },
    price: { status: "numeric", amount: "96000", currency: "UZS" },
    out_of_stock: false,
    image: { url: `/media/${partial.slug}.png`, alt: partial.model_display, width: null, height: null, is_primary: true },
    ...partial,
  };
}

function category(slug: string, count: number): CategoryNode {
  return { slug, name: slug, description: null, translation_fallback: false, product_count: count, children: [] };
}

test("a photographed product with a model code is preferred over an earlier item without one", () => {
  const cloud = card({
    slug: "cloud",
    model_display: "7-дневная видеоистория событий",
    image: { url: "/media/cloud.png", alt: "", width: null, height: null, is_primary: true },
  });
  const camera = card({ slug: "cs-c60p", model_display: "CS-C60P (3MP)" });
  const picked = pickCategoryProduct([cloud, camera], new Set());
  assert.equal(picked?.slug, "cs-c60p");
});

test("the same photograph is not used for two homepage products", () => {
  const shared = { url: "/media/shared.png", alt: "", width: null, height: null, is_primary: true };
  const hero = card({ slug: "hero", model_display: "DS-2CD1023G2-LIU", image: shared });
  const duplicate = card({ slug: "copy", model_display: "IPC-B129HA-LU", image: shared });
  const recorder = card({ slug: "nvr", model_display: "DS-7104NI-Q1" });
  const selected = selectHomepageProducts([hero], [[duplicate, recorder]]);
  assert.equal(selected.hero?.slug, "hero");
  assert.deepEqual(selected.featured.map((product) => product.slug), ["nvr"]);
});

test("a product without a photo is not featured while a later photo in the same group can be", () => {
  const blank = card({ slug: "blank", model_display: "DS-1280ZJ-XS", image: null });
  const photo = card({ slug: "poe", model_display: "SMART-04-POE" });
  const selected = selectHomepageProducts([], [[blank, photo]]);
  assert.equal(selected.hero, null);
  assert.equal(selected.featured[0]?.slug, "poe");
});

test("category shortcuts keep only published sections and leave the rest in catalog order", () => {
  const categories = [category("skud", 71), category("ip-kamery", 116), category("hdd", 11)];
  const split = splitCategories(categories, ["ip-kamery", "missing", "skud"]);
  assert.deepEqual(split.shortcuts.map((item) => item.slug), ["ip-kamery", "skud"]);
  assert.deepEqual(split.rest.map((item) => item.slug), ["hdd"]);
  assert.equal(split.shortcuts[0]?.product_count, 116);
});
