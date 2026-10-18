import assert from "node:assert/strict";
import test from "node:test";

import {
  billingPeriod,
  catalogDestinations,
  isServicePlan,
  listingHasActiveFilter,
  showOriginalNote,
} from "./presentation.ts";

test("a model code does not get a Russian-title note, and Russian wording does", () => {
  assert.equal(showOriginalNote(true, "IPC-D160HA-LU"), false);
  assert.equal(showOriginalNote(true, "BNC"), false);
  assert.equal(showOriginalNote(false, "Купольная"), false);
  assert.equal(showOriginalNote(true, "7-дневная видеоистория событий"), true);
  assert.equal(showOriginalNote(true, "   "), false);
});

test("monthly and yearly billing labels are recognized, and other options stay ordinary", () => {
  assert.equal(billingPeriod("Ежемесячно:"), "monthly");
  assert.equal(billingPeriod("Ежегодно:"), "yearly");
  assert.equal(billingPeriod("с солнечной панель"), null);
  assert.equal(billingPeriod(null), null);
});

test("a service plan is a service record or, before that field arrives, a billing option", () => {
  assert.equal(isServicePlan({ product_kind: "service", option_label: "Ежемесячно:" }), true);
  assert.equal(isServicePlan({ product_kind: "product", option_label: "Ежемесячно:" }), false);
  assert.equal(isServicePlan({ option_label: "Ежегодно:" }), true);
  assert.equal(isServicePlan({ option_label: "с солнечной панель" }), false);
});

test("brand and category links stay distinct and the same destination is not repeated", () => {
  const labeled = catalogDestinations(
    "ru",
    { slug: "ezviz", name: "EZVIZ" },
    { slug: "ezviz", parent_slug: null, name: "EZVIZ" },
  );
  assert.deepEqual(
    labeled.map((link) => [link.kind, link.href]),
    [
      ["brand", "/ru/brands/ezviz"],
      ["category", "/ru/categories/ezviz"],
    ],
  );
  const repeated = catalogDestinations(
    "en",
    { slug: "hikvision", name: "Hikvision" },
    { slug: "hikvision", parent_slug: "brands", name: "Hikvision" },
  );
  assert.equal(repeated.length, 2);
  assert.notEqual(repeated[0].href, repeated[1].href);
  assert.deepEqual(catalogDestinations("en", { slug: "only", name: "Only" }, null), [
    { kind: "brand", href: "/en/brands/only", name: "Only" },
  ]);
});

test("a plain catalog page does not announce a result count, and a search does", () => {
  assert.equal(listingHasActiveFilter({}), false);
  assert.equal(listingHasActiveFilter({ category: "nvr", lockedCategory: true }), false);
  assert.equal(listingHasActiveFilter({ q: "BNC" }), true);
  assert.equal(listingHasActiveFilter({ brand: "seagate" }), true);
  assert.equal(listingHasActiveFilter({ brand: "seagate", lockedBrand: true }), false);
  assert.equal(listingHasActiveFilter({ minPrice: "10" }), true);
});
