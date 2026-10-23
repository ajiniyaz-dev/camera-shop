import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { descriptionLayout, descriptionParagraphs, descriptionPreview } from "./product-description.ts";

describe("descriptionParagraphs", () => {
  it("yields nothing for missing or blank text", () => {
    assert.deepEqual(descriptionParagraphs(null), []);
    assert.deepEqual(descriptionParagraphs(undefined), []);
    assert.deepEqual(descriptionParagraphs("   \n  "), []);
  });

  it("keeps a single short sentence intact", () => {
    assert.deepEqual(descriptionParagraphs("4 MP turret camera with ColorVu."), [
      "4 MP turret camera with ColorVu.",
    ]);
  });

  it("does not split a compact spec sentence on commas or units", () => {
    const text =
      "Power supply, operating voltage: 110V/220V ± 15%, output voltage: 12V, output current: 40A.";
    assert.deepEqual(descriptionParagraphs(text), [text]);
  });

  it("does not treat codec versions as sentence boundaries", () => {
    const text = "Supports H.265 and H.264 compression with 2.0 MP resolution.";
    assert.deepEqual(descriptionParagraphs(text), [text]);
  });

  it("presents a series of meaningful sentences as separate paragraphs", () => {
    const text =
      "Two-sided fingerprint scanner. Fingerprint unlocking. Password and contactless-card unlocking.";
    assert.deepEqual(descriptionParagraphs(text), [
      "Two-sided fingerprint scanner.",
      "Fingerprint unlocking.",
      "Password and contactless-card unlocking.",
    ]);
  });

  it("preserves explicit line breaks, including Windows newlines", () => {
    const text = "Passage width: 600-900 mm\r\nInput voltage: 100-240 V\nMotor type: DC brush motor";
    assert.deepEqual(descriptionParagraphs(text), [
      "Passage width: 600-900 mm",
      "Input voltage: 100-240 V",
      "Motor type: DC brush motor",
    ]);
  });

  it("preserves explicitly marked bullet phrases", () => {
    assert.deepEqual(descriptionParagraphs("Metal housing • IP67 • 12 V DC"), [
      "Metal housing",
      "IP67",
      "12 V DC",
    ]);
  });

  it("splits Cyrillic sentences without rewriting them", () => {
    assert.deepEqual(descriptionParagraphs("Двусторонний сканер. Разблокировка по отпечатку."), [
      "Двусторонний сканер.",
      "Разблокировка по отпечатку.",
    ]);
  });
});

describe("descriptionLayout", () => {
  it("keeps a single block as a paragraph", () => {
    assert.equal(descriptionLayout(["Power supply, operating voltage: 12V 40A."]), "paragraphs");
  });

  it("lists several short distinct points", () => {
    assert.equal(
      descriptionLayout([
        "Two-sided fingerprint scanner.",
        "Fingerprint unlocking.",
        "Password and contactless-card unlocking.",
      ]),
      "list",
    );
  });

  it("lists explicit label-and-value lines", () => {
    assert.equal(
      descriptionLayout(["Passage width: 600-900 mm", "Input voltage: 100-240 V", "Motor type: DC brush motor"]),
      "list",
    );
  });

  it("does not force two longer sentences into a list", () => {
    assert.equal(
      descriptionLayout([
        "Waterproof analog kit for a villa or a home, only one call button.",
        "The kit includes DS-KB2421-IM and DS-KH 2220 with a 5-meter 4-wire cable.",
      ]),
      "paragraphs",
    );
  });
});

describe("descriptionPreview", () => {
  it("does not render text or a toggle for missing descriptions", () => {
    assert.deepEqual(descriptionPreview(null, false), { text: "", hasMore: false });
    assert.deepEqual(descriptionPreview("  \n ", false), { text: "", hasMore: false });
  });

  it("keeps a short description intact without a toggle", () => {
    assert.deepEqual(descriptionPreview("Compact camera description.", false), {
      text: "Compact camera description.",
      hasMore: false,
    });
  });

  it("uses a compact collapsed excerpt and a longer expanded excerpt", () => {
    const description = "Security camera details. ".repeat(40);
    const collapsed = descriptionPreview(description, false);
    const expanded = descriptionPreview(description, true);
    assert.equal(collapsed.hasMore, true);
    assert.equal(expanded.hasMore, true);
    assert.ok(collapsed.text.length < expanded.text.length);
    assert.ok(collapsed.text.endsWith("…"));
    assert.ok(expanded.text.endsWith("…"));
  });
});
