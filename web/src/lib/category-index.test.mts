import assert from "node:assert/strict";
import test from "node:test";

import type { CategoryNode } from "./public-api.ts";

/** Pure helpers mirroring CategoryIndex hierarchy rules for regression tests. */

export function parentCards(nodes: CategoryNode[]): CategoryNode[] {
  return nodes;
}

export function childChips(node: CategoryNode): Array<{ slug: string; name: string }> {
  return node.children.map((child) => ({ slug: child.slug, name: child.name }));
}

export function categoryHref(locale: string, parent: string, child?: string): string {
  return child ? `/${locale}/categories/${parent}/${child}` : `/${locale}/categories/${parent}`;
}

test("parent cards keep leaf and branched categories in one flat list", () => {
  const nodes: CategoryNode[] = [
    { slug: "hdd", name: "HDD", description: null, translation_fallback: false, product_count: 16, children: [] },
    {
      slug: "dvr",
      name: "DVR",
      description: null,
      translation_fallback: false,
      product_count: 8,
      children: [
        {
          slug: "u-seriya",
          name: "U",
          description: null,
          translation_fallback: false,
          product_count: 3,
          children: [],
        },
      ],
    },
  ];
  assert.equal(parentCards(nodes).length, 2);
  assert.deepEqual(childChips(nodes[0]!), []);
  assert.deepEqual(childChips(nodes[1]!), [{ slug: "u-seriya", name: "U" }]);
});

test("category hrefs stay under the existing locale category routes", () => {
  assert.equal(categoryHref("uz", "turbo-hd-kamera"), "/uz/categories/turbo-hd-kamera");
  assert.equal(categoryHref("ru", "dvr", "edvr"), "/ru/categories/dvr/edvr");
  assert.equal(categoryHref("en", "nvr", "mh-seriya"), "/en/categories/nvr/mh-seriya");
});
