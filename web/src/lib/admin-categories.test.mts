import assert from "node:assert/strict";
import test from "node:test";

import { ApiError } from "./admin-api.ts";
import { CategoryListError, categoryLoadFailure, parseCategoryList } from "./admin-categories.ts";

const category = {
  id: 4,
  parent_id: null,
  name_ru: "Камеры",
  name_uz: null,
  name_en: null,
  is_published: false,
};

test("parseCategoryList reads a category array", () => {
  assert.deepEqual(parseCategoryList({ categories: [category, { ...category, id: 5, parent_id: 4 }] }), [
    category,
    { ...category, id: 5, parent_id: 4 },
  ]);
});

test("parseCategoryList rejects a missing, non-array, or malformed list", () => {
  assert.throws(() => parseCategoryList(null), CategoryListError);
  assert.throws(() => parseCategoryList({}), CategoryListError);
  assert.throws(() => parseCategoryList({ categories: null }), CategoryListError);
  assert.throws(() => parseCategoryList({ categories: [{ ...category, name_ru: 12 }] }), CategoryListError);
  assert.throws(() => parseCategoryList({ categories: [{ ...category, id: "4" }] }), CategoryListError);
});

test("categoryLoadFailure distinguishes authentication, request, and network errors", () => {
  assert.equal(categoryLoadFailure(new ApiError(401, "Authentication is required.")), "unauthorized");
  assert.equal(categoryLoadFailure(new ApiError(500, "The request could not be completed.")), "message");
  assert.equal(categoryLoadFailure(new ApiError(502, "   ")), "failed");
  assert.equal(categoryLoadFailure(new TypeError("Failed to fetch")), "failed");
  assert.equal(categoryLoadFailure(new CategoryListError()), "failed");
});
