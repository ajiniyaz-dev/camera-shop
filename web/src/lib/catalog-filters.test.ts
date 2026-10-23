import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  categoryValue,
  groupCatalogCategories,
  listingHref,
  pageWindow,
  parsePageInput,
  parsePageParam,
  parsePageSize,
  resultRange,
} from "./catalog-filters.ts";

describe("catalog-filters", () => {
  it("encodes nested category values", () => {
    assert.equal(categoryValue("colorvu"), "colorvu");
    assert.equal(categoryValue("acusense-dvr", "dvr"), "dvr/acusense-dvr");
    assert.equal(categoryValue(), "");
  });

  it("groups published categories under their parents", () => {
    const groups = groupCatalogCategories([
      { slug: "dvr", parent_slug: null, name: "DVR" },
      { slug: "acusense-dvr", parent_slug: "dvr", name: "AcuSense DVR" },
      { slug: "ip-kamery", parent_slug: null, name: "IP cameras" },
    ]);
    assert.equal(groups.length, 2);
    assert.equal(groups[0]?.slug, "dvr");
    assert.deepEqual(
      groups[0]?.children.map((item) => item.slug),
      ["acusense-dvr"],
    );
    assert.deepEqual(groups[1]?.children, []);
  });

  it("keeps listing links on the current path and omits empty params", () => {
    assert.equal(listingHref("/en/catalog", { q: "nvr", sort: undefined }, 1), "/en/catalog?q=nvr");
    assert.equal(
      listingHref("/uz/catalog", { brand: "hikvision", category: "ip-kamery" }, 3),
      "/uz/catalog?brand=hikvision&category=ip-kamery&page=3",
    );
  });

  it("computes the visible result range from pagination", () => {
    assert.deepEqual(resultRange(1, 24, 100), { from: 1, to: 24 });
    assert.deepEqual(resultRange(5, 24, 100), { from: 97, to: 100 });
    assert.equal(resultRange(1, 24, 0), null);
  });

  it("parses page and page-size query values safely", () => {
    assert.equal(parsePageParam(undefined), 1);
    assert.equal(parsePageParam("2"), 2);
    assert.equal(parsePageParam("0"), 1);
    assert.equal(parsePageParam("-3"), 1);
    assert.equal(parsePageParam("abc"), 1);
    assert.equal(parsePageSize("12"), 12);
    assert.equal(parsePageSize("48"), 48);
    assert.equal(parsePageSize("10"), 24);
    assert.equal(parsePageSize("nope"), 24);
  });

  it("clamps a go-to-page value and rejects malformed input", () => {
    assert.deepEqual(parsePageInput("3", 10), { status: "valid", page: 3 });
    assert.deepEqual(parsePageInput("99", 10), { status: "valid", page: 10 });
    assert.deepEqual(parsePageInput("0", 10), { status: "invalid" });
    assert.deepEqual(parsePageInput("two", 10), { status: "invalid" });
    assert.deepEqual(parsePageInput("  ", 10), { status: "empty" });
  });

  it("builds a compact page window with ellipses", () => {
    assert.deepEqual(pageWindow(1, 4), [1, 2, 3, 4]);
    assert.deepEqual(pageWindow(5, 27), [1, "ellipsis", 4, 5, 6, "ellipsis", 27]);
    assert.deepEqual(pageWindow(1, 27), [1, 2, "ellipsis", 27]);
    assert.deepEqual(pageWindow(27, 27), [1, "ellipsis", 26, 27]);
  });
});
