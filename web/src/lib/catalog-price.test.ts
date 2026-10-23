import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { appliedCatalogPrice, catalogPriceIssue, parseCatalogPrice } from "./catalog-price.ts";

describe("parseCatalogPrice", () => {
  it("treats empty and whitespace as empty", () => {
    assert.deepEqual(parseCatalogPrice(undefined), { status: "empty" });
    assert.deepEqual(parseCatalogPrice(""), { status: "empty" });
    assert.deepEqual(parseCatalogPrice("   "), { status: "empty" });
  });

  it("accepts whole non-negative prices", () => {
    assert.deepEqual(parseCatalogPrice("0"), { status: "valid", value: "0" });
    assert.deepEqual(parseCatalogPrice("400000"), { status: "valid", value: "400000" });
    assert.deepEqual(parseCatalogPrice(" 01 "), { status: "valid", value: "1" });
  });

  it("rejects letters, symbols, decimals, and negatives", () => {
    for (const value of ["abc", "12a", "1e3", "15.5", "12,5", "-1", "+4", "Infinity", "NaN", "1.0"]) {
      assert.equal(parseCatalogPrice(value).status, "invalid", value);
    }
  });

  it("does not coerce invalid input to zero", () => {
    assert.notDeepEqual(parseCatalogPrice("nope"), { status: "valid", value: "0" });
    assert.notDeepEqual(parseCatalogPrice("-0"), { status: "valid", value: "0" });
  });
});

describe("catalogPriceIssue", () => {
  it("allows a single bound or two empty fields", () => {
    assert.equal(catalogPriceIssue(parseCatalogPrice(""), parseCatalogPrice("")), null);
    assert.equal(catalogPriceIssue(parseCatalogPrice("100"), parseCatalogPrice("")), null);
    assert.equal(catalogPriceIssue(parseCatalogPrice(""), parseCatalogPrice("100")), null);
    assert.equal(catalogPriceIssue(parseCatalogPrice("100"), parseCatalogPrice("100")), null);
  });

  it("rejects a minimum greater than the maximum", () => {
    assert.equal(catalogPriceIssue(parseCatalogPrice("200"), parseCatalogPrice("100")), "range");
  });

  it("rejects a malformed field even when the other bound is valid", () => {
    assert.equal(catalogPriceIssue(parseCatalogPrice("abc"), parseCatalogPrice("100")), "invalid");
    assert.equal(catalogPriceIssue(parseCatalogPrice("10"), parseCatalogPrice("-3")), "invalid");
  });

  it("drops both bounds when the range is inverted", () => {
    const min = parseCatalogPrice("200");
    const max = parseCatalogPrice("100");
    const issue = catalogPriceIssue(min, max);
    assert.equal(appliedCatalogPrice(min, issue), undefined);
    assert.equal(appliedCatalogPrice(max, issue), undefined);
  });
});
