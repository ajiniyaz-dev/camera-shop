import assert from "node:assert/strict";
import test from "node:test";

import { isOtherBrand, schemaBrand } from "./other-brand.ts";

test("real brands stay manufacturers and Other stays a label", () => {
  assert.equal(isOtherBrand(null), false);
  assert.equal(isOtherBrand({ slug: "hikvision", name: "Hikvision" }), false);
  assert.deepEqual(schemaBrand({ slug: "hikvision", name: "Hikvision" }), {
    "@type": "Brand",
    name: "Hikvision",
  });
  assert.equal(schemaBrand(null), null);
});

test("Other is recognised by its slug or stored label and is not a manufacturer", () => {
  for (const brand of [
    { slug: "other", name: "Other" },
    { slug: "other", name: "Другие" },
    { slug: "drugie", name: "Другие" },
    { slug: "spare", name: "Boshqalar" },
    { slug: "other", name: "  Other  " },
  ]) {
    assert.equal(isOtherBrand(brand), true);
    assert.equal(schemaBrand(brand), null);
  }
  assert.equal(isOtherBrand({ slug: "hikvision", name: "другие устройства" }), false);
});
