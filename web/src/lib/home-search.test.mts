import assert from "node:assert/strict";
import test from "node:test";

import { categoryMark } from "./home-category.ts";
import {
  activeTarget,
  allResultsPath,
  loadSuggestions,
  moveActive,
  productPath,
  productsSearchPath,
  searchPlan,
  SearchGeneration,
  showAllResults,
  suggestionOptionCount,
} from "./home-search.ts";
import { formatPublicPrice } from "./price-format.ts";
import { messages } from "./public-i18n.ts";

const sample = {
  slug: "hikvision-ds-2cd",
  name: "DS-2CD",
  model_display: "DS-2CD",
  option_label: null,
  brand: { name: "Hikvision" },
  category: { name: "IP" },
  price: { status: "on_request", amount: null },
  image: null,
};

test("the first non-whitespace character starts a search and blank input does not", () => {
  assert.deepEqual(searchPlan("  d  "), { term: "d", delay: 250 });
  assert.deepEqual(searchPlan(" DS-2CD "), { term: "DS-2CD", delay: 250 });
  assert.deepEqual(searchPlan(""), { term: null, delay: 0 });
  assert.deepEqual(searchPlan("   "), { term: null, delay: 0 });
  assert.equal(searchPlan("x".repeat(100)).term?.length, 80);
});

test("suggestions request only the published public catalog", () => {
  const path = productsSearchPath("uz", "DS 2");
  const params = new URLSearchParams(path.split("?")[1]);
  assert.equal(path.startsWith("/api/public/products?"), true);
  assert.equal(params.get("locale"), "uz");
  assert.equal(params.get("q"), "DS 2");
  assert.equal(params.get("page_size"), "6");
  assert.equal(params.get("catalog_status"), null);
  assert.equal(path.includes("admin"), false);
  assert.equal(path.includes("draft"), false);
});

test("an older request cannot replace a newer one", () => {
  const session = new SearchGeneration();
  const first = session.next();
  const second = session.next();
  assert.equal(session.isCurrent(first), false);
  assert.equal(session.isCurrent(second), true);
  session.next();
  assert.equal(session.isCurrent(second), false);
});

test("keyboard movement wraps suggestions and the all-results action", () => {
  assert.equal(moveActive(-1, 0, "ArrowDown"), -1);
  assert.equal(moveActive(-1, 3, "ArrowDown"), 0);
  assert.equal(moveActive(2, 3, "ArrowDown"), 0);
  assert.equal(moveActive(0, 3, "ArrowUp"), 2);
  assert.equal(moveActive(1, 3, "ArrowUp"), 0);
  assert.equal(suggestionOptionCount(2, true), 3);
  assert.equal(suggestionOptionCount(0, false), 0);
});

test("the active row opens the product or the full search in the current language", () => {
  assert.equal(productPath("en", "a b"), "/en/products/a%20b");
  assert.equal(allResultsPath("ru", "DS 2"), "/ru/search?q=DS%202");
  assert.equal(activeTarget(0, [sample], true, "uz", "DS"), "/uz/products/hikvision-ds-2cd");
  assert.equal(activeTarget(1, [sample], true, "ru", "DS"), "/ru/search?q=DS");
  assert.equal(activeTarget(-1, [sample], true, "en", "DS"), null);
  assert.equal(showAllResults("ready", 1), true);
  assert.equal(showAllResults("empty", 0), false);
  assert.equal(showAllResults("error", 4), false);
});

test("prices and new labels stay localized", () => {
  assert.equal(formatPublicPrice({ status: "numeric", amount: "78800", currency: "UZS" }, "ru"), "78 800 сум");
  assert.equal(formatPublicPrice({ status: "on_request", amount: null, currency: null }, "ru"), messages.ru.onRequest);
  assert.equal(formatPublicPrice({ status: "on_request", amount: null, currency: null }, "uz"), messages.uz.onRequest);
  assert.equal(formatPublicPrice({ status: "on_request", amount: null, currency: null }, "en"), messages.en.onRequest);
  assert.equal(formatPublicPrice({ status: "hidden", amount: null, currency: null }, "en"), "");
  assert.equal(formatPublicPrice({ status: "unavailable", amount: null, currency: null }, "en"), messages.en.priceUnavailable);
  assert.notEqual(messages.ru.viewAllResults, messages.en.viewAllResults);
  assert.notEqual(messages.uz.allCategories, messages.en.allCategories);
  assert.notEqual(messages.ru.featuredIntro, messages.en.featuredIntro);
  assert.notEqual(messages.ru.viewProduct, messages.uz.viewProduct);
  for (const locale of ["ru", "uz", "en"] as const) {
    assert.ok(messages[locale].viewAllResults);
    assert.ok(messages[locale].allCategories);
  }
});

test("public copy keeps the catalog description and drops order-payment disclaimers", () => {
  assert.equal(
    messages.en.heroText,
    "A catalog of video surveillance equipment, security equipment, and related services.",
  );
  assert.equal(
    messages.ru.heroText,
    "Каталог оборудования для видеонаблюдения, систем безопасности и связанных услуг.",
  );
  assert.equal(messages.uz.heroText, "Videokuzatuv, xavfsizlik uskunalari va tegishli xizmatlar katalogi.");
  assert.equal(
    messages.en.selectionNote,
    "Your cart is saved in this browser. Use it to prepare your product inquiry.",
  );
  assert.equal(
    messages.ru.selectionNote,
    "Корзина сохраняется в этом браузере. Используйте её, чтобы подготовить запрос по товарам.",
  );
  assert.equal(
    messages.uz.selectionNote,
    "Savatcha shu brauzerda saqlanadi. Undan mahsulotlar bo\u2018yicha so\u2018rov tayyorlash uchun foydalaning.",
  );
  for (const locale of ["ru", "uz", "en"] as const) {
    assert.equal("catalogPurpose" in messages[locale], false);
    assert.match(messages[locale].heroText, /katalog|catalog|Каталог/i);
    assert.doesNotMatch(messages[locale].heroText, /orders or payments|не оформляются|qabul qilinmaydi/i);
    assert.doesNotMatch(messages[locale].selectionNote, /not an order|не заказ|buyurtma yoki to/i);
  }
});

test("a failed or empty catalog response is reported and drafts are not added by the client", async () => {
  const calls: string[] = [];
  const ok = async (input: RequestInfo | URL) => {
    calls.push(String(input));
    return new Response(JSON.stringify({ products: [], total: 0 }), { status: 200, headers: { "content-type": "application/json" } });
  };
  const empty = await loadSuggestions("en", "z", new AbortController().signal, ok as typeof fetch);
  assert.deepEqual(empty, { products: [], total: 0 });
  assert.equal(calls[0]?.includes("/api/public/products?"), true);

  const failed = async () => new Response("no", { status: 500 });
  await assert.rejects(() => loadSuggestions("ru", "z", new AbortController().signal, failed as typeof fetch));
});

test("category marks follow the equipment type and stay neutral when the type is unknown", () => {
  assert.equal(categoryMark("hdd"), "disk");
  assert.equal(categoryMark("bloki-pitaniya"), "power");
  assert.equal(categoryMark("kabeli-i-razyomy"), "cable");
  assert.equal(categoryMark("ip-kamery"), "camera");
  assert.equal(categoryMark("skud"), "access");
  assert.equal(categoryMark("proektnoe-oborudovanie"), "neutral");
  assert.notEqual(categoryMark("kommunikatsionnye-shkafy"), "camera");
  assert.notEqual(categoryMark("zvukovoe-oborudovanie"), "camera");
});
