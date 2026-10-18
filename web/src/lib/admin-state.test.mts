import assert from "node:assert/strict";
import test from "node:test";

import { canSaveLoadedProduct, listStatus } from "./admin-state.ts";

test("an existing product cannot be saved before its record loads", () => {
  assert.equal(canSaveLoadedProduct(12, false), false);
  assert.equal(canSaveLoadedProduct(12, true), true);
  assert.equal(canSaveLoadedProduct(undefined, false), true);
});

test("an empty admin list is loading or failed before it is reported empty", () => {
  assert.equal(listStatus(true, false, 0), "loading");
  assert.equal(listStatus(false, true, 0), "error");
  assert.equal(listStatus(false, false, 0), "empty");
  assert.equal(listStatus(true, false, 3), "ready");
});
