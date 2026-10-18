import assert from "node:assert/strict";
import test from "node:test";

import {
  addToSelection,
  normalizeSelection,
  removeFromSelection,
  SELECTION_LIMIT,
  selectionBadgeCount,
  selectionNavHref,
  selectionNavLabel,
} from "./selection.ts";

test("a selection keeps unique valid slugs and drops stale shapes", () => {
  assert.deepEqual(normalizeSelection(["bnc", "bnc", " IPC ", 4, "../secret", "ds-2cd2143"]), ["bnc", "ds-2cd2143"]);
  assert.deepEqual(normalizeSelection({ slug: "bnc" }), []);
  assert.equal(normalizeSelection(Array.from({ length: 60 }, (_, index) => `item-${index}`)).length, SELECTION_LIMIT);
});

test("adding a product twice keeps one entry, and a full selection does not grow", () => {
  const first = addToSelection([], "ezviz-7-dnevnaya-videoistoriya-sobytiy-ezhemesyachno");
  assert.equal(first.status, "added");
  const again = addToSelection(first.slugs, "ezviz-7-dnevnaya-videoistoriya-sobytiy-ezhemesyachno");
  assert.equal(again.status, "present");
  assert.equal(again.slugs.length, 1);
  const full = addToSelection(
    Array.from({ length: SELECTION_LIMIT }, (_, index) => `item-${index}`),
    "one-more",
  );
  assert.equal(full.status, "full");
  assert.equal(full.slugs.length, SELECTION_LIMIT);
  assert.equal(addToSelection([], "bad slug").status, "invalid");
});

test("removing a product updates the list and ignores a missing slug", () => {
  assert.deepEqual(removeFromSelection(["one", "two", "one"], "one"), ["two"]);
  assert.deepEqual(removeFromSelection(["one"], "missing"), ["one"]);
});

test("selection nav href points at the localized cart page", () => {
  assert.equal(selectionNavHref("ru"), "/ru/cart");
  assert.equal(selectionNavHref("uz"), "/uz/cart");
  assert.equal(selectionNavHref("en"), "/en/cart");
});

test("selection nav label and badge count cover empty and filled carts", () => {
  assert.equal(selectionNavLabel("Корзина", 0), "Корзина: 0");
  assert.equal(selectionNavLabel("Savatcha", 1), "Savatcha: 1");
  assert.equal(selectionNavLabel("Cart", 3), "Cart: 3");
  assert.equal(selectionBadgeCount([]), 0);
  assert.equal(selectionBadgeCount(["a", "a", "b"]), 2);
  assert.equal(selectionBadgeCount(["bad slug", "ok-item"]), 1);
});

test("badge count stays in sync after add and remove without duplicating", () => {
  let slugs: string[] = [];
  assert.equal(selectionBadgeCount(slugs), 0);
  assert.equal(selectionNavLabel("Cart", selectionBadgeCount(slugs)), "Cart: 0");

  const first = addToSelection(slugs, "hilook-ipc-b469had-luf-sl");
  assert.equal(first.status, "added");
  slugs = first.slugs;
  assert.equal(selectionBadgeCount(slugs), 1);
  assert.equal(selectionNavLabel("Корзина", selectionBadgeCount(slugs)), "Корзина: 1");

  const again = addToSelection(slugs, "hilook-ipc-b469had-luf-sl");
  assert.equal(again.status, "present");
  slugs = again.slugs;
  assert.equal(selectionBadgeCount(slugs), 1);

  const second = addToSelection(slugs, "ezviz-cs-c60p-3mp");
  assert.equal(second.status, "added");
  slugs = second.slugs;
  assert.equal(selectionBadgeCount(slugs), 2);
  assert.equal(selectionNavHref("uz"), "/uz/cart");
  assert.equal(selectionNavLabel("Savatcha", selectionBadgeCount(slugs)), "Savatcha: 2");

  slugs = removeFromSelection(slugs, "hilook-ipc-b469had-luf-sl");
  assert.equal(selectionBadgeCount(slugs), 1);
  slugs = removeFromSelection(slugs, "ezviz-cs-c60p-3mp");
  assert.equal(selectionBadgeCount(slugs), 0);
  assert.equal(selectionNavLabel("Cart", selectionBadgeCount(slugs)), "Cart: 0");
});
