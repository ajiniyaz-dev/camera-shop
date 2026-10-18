import assert from "node:assert/strict";
import test from "node:test";

import { productPhotoAttributes, productPhotoClassName } from "./product-photo.ts";

test("a photo keeps its real pixel size and does not invent a large stand-in", () => {
  assert.deepEqual(productPhotoAttributes(63, 38), { width: 63, height: 38 });
  assert.deepEqual(productPhotoAttributes(1600, 1200), { width: 1600, height: 1200 });
  assert.deepEqual(productPhotoAttributes(null, null), {});
  assert.deepEqual(productPhotoAttributes(undefined, 400), {});
  assert.deepEqual(productPhotoAttributes(0, 400), {});
});

test("photos stay contained inside the frame and are not forced to its width", () => {
  for (const name of [productPhotoClassName(), productPhotoClassName("gallery")]) {
    const classes = name.split(/\s+/);
    assert.equal(classes.includes("object-contain"), true);
    assert.equal(classes.includes("w-auto"), true);
    assert.equal(classes.includes("h-auto"), true);
    assert.equal(classes.includes("w-full"), false);
    assert.equal(classes.includes("object-cover"), false);
  }
  assert.match(productPhotoClassName("gallery"), /max-h-\[32rem\]/);
  assert.match(productPhotoClassName(), /max-h-full/);
});
