import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  LANDING_CATEGORY_SLUGS,
  LANDING_SOLUTIONS,
  LANDING_SYSTEM_PARTS,
  LANDING_TECHNOLOGIES,
  availableLandingCategories,
  categoryHref,
  firstCategoryHref,
  techHref,
  type LandingCategoryRef,
} from "./home-landing.ts";

function refs(entries: Array<[string, string | null]>): Map<string, LandingCategoryRef> {
  return availableLandingCategories(
    entries.map(([slug, parentSlug]) => ({
      slug,
      name: slug,
      parentSlug,
    })),
  );
}

const published = refs(Object.values(LANDING_CATEGORY_SLUGS).map((slug) => [slug, null] as [string, string | null]));

describe("home-landing category links", () => {
  it("resolves only slugs present in the available set", () => {
    assert.equal(categoryHref("en", "colorvu", published), "/en/categories/colorvu");
    assert.equal(categoryHref("en", "missing-slug", published), null);
  });

  it("includes the parent segment for nested categories", () => {
    const nested = refs([["acusense-dvr", "dvr"]]);
    assert.equal(categoryHref("en", "acusense-dvr", nested), "/en/categories/dvr/acusense-dvr");
  });

  it("maps ColorVu and AcuSense to verified catalog sections", () => {
    const withAcusense = refs([
      ["colorvu", null],
      ["acusense-dvr", "dvr"],
    ]);
    const colorvu = LANDING_TECHNOLOGIES.find((item) => item.id === "colorvu");
    const acusense = LANDING_TECHNOLOGIES.find((item) => item.id === "acusense");
    assert.deepEqual(techHref(colorvu!, "ru", withAcusense), {
      href: "/ru/categories/colorvu",
      kind: "category",
    });
    assert.deepEqual(techHref(acusense!, "uz", withAcusense), {
      href: "/uz/categories/dvr/acusense-dvr",
      kind: "category",
    });
  });

  it("does not invent a DarkFighter category link", () => {
    const darkfighter = LANDING_TECHNOLOGIES.find((item) => item.id === "darkfighter");
    assert.equal(techHref(darkfighter!, "en", published), null);
  });

  it("routes Hik-Connect to the contact page", () => {
    const hikconnect = LANDING_TECHNOLOGIES.find((item) => item.id === "hikconnect");
    assert.deepEqual(techHref(hikconnect!, "en", published), {
      href: "/en/contact",
      kind: "contact",
    });
  });

  it("keeps solution and system links within verified slugs", () => {
    for (const solution of LANDING_SOLUTIONS) {
      const href = firstCategoryHref("en", solution.categorySlugs, published);
      assert.ok(href, `solution ${solution.id} should resolve`);
      assert.match(href!, /^\/en\/categories\//);
    }
    for (const part of LANDING_SYSTEM_PARTS) {
      const href = firstCategoryHref("en", part.categorySlugs, published);
      assert.ok(href, `system part ${part.id} should resolve`);
    }
  });

  it("hides links when the live catalog lacks the section", () => {
    const empty = availableLandingCategories([]);
    assert.equal(firstCategoryHref("en", LANDING_SOLUTIONS[0].categorySlugs, empty), null);
    assert.equal(categoryHref("en", "hdd", empty), null);
  });
});
