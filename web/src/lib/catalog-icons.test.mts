import assert from "node:assert/strict";
import test from "node:test";

import { categoryMark, type CategoryMark } from "./home-category.ts";

/**
 * Mirrors `CATEGORY_ICONS` keys in catalog-icons.tsx without importing React/Lucide
 * so Node library tests stay free of JSX tooling.
 */
const MARKS: CategoryMark[] = [
  "disk",
  "power",
  "rack",
  "cable",
  "filter",
  "router",
  "switch",
  "intercom",
  "recorder",
  "ptz",
  "audio",
  "access",
  "bracket",
  "camera",
  "neutral",
];

test("every category mark used for Lucide icons is reachable from a known slug", () => {
  const samples: Record<CategoryMark, string> = {
    disk: "hdd",
    power: "bloki-pitaniya",
    rack: "kommunikatsionnye-shkafy",
    cable: "kabeli-i-razyomy",
    filter: "setevye-filtry",
    router: "4g-marshrutizatory",
    switch: "poe-kommutatory",
    intercom: "domofony",
    recorder: "nvr",
    ptz: "ptz",
    audio: "zvukovoe-oborudovanie",
    access: "skud",
    bracket: "montazhnye-prinadlezhnosti",
    camera: "ip-kamery",
    neutral: "proektnoe-oborudovanie",
  };
  for (const mark of MARKS) {
    assert.equal(categoryMark(samples[mark]), mark, mark);
  }
});

test("ambiguous project equipment stays neutral and does not invent a camera icon", () => {
  assert.equal(categoryMark("proektnoe-oborudovanie"), "neutral");
  assert.equal(categoryMark("drugie-ustroystva"), "neutral");
});
