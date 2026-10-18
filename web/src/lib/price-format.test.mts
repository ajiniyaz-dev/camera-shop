import assert from "node:assert/strict";
import test from "node:test";

import { formatPublicPrice, formatUzsAmount, selectionTotal } from "./price-format.ts";

test("UZS amounts are grouped for each language and are not converted again", () => {
  assert.equal(formatUzsAmount("4800000", "ru"), "4 800 000 сум");
  assert.equal(formatUzsAmount("4800000", "uz"), "4 800 000 soʻm");
  assert.equal(formatUzsAmount("4800000", "en"), "4,800,000 UZS");
  assert.equal(formatUzsAmount("1104000", "ru"), "1 104 000 сум");
  // The API already returned soʻm. Formatting must not multiply again.
  assert.notEqual(formatUzsAmount("4800000", "en"), "46,080,000,000 UZS");
});

test("public price labels cover numeric, on-request, and unavailable states", () => {
  assert.equal(
    formatPublicPrice({ status: "numeric", amount: "221400", currency: "UZS" }, "en"),
    "221,400 UZS",
  );
  assert.equal(formatPublicPrice({ status: "on_request", amount: null, currency: null }, "ru"), "По запросу");
  assert.equal(formatPublicPrice({ status: "unavailable", amount: null, currency: null }, "uz"), "Narx mavjud emas");
  assert.equal(formatPublicPrice({ status: "hidden", amount: null, currency: null }, "en"), "");
  assert.equal(formatPublicPrice({ status: "numeric", amount: "20.50", currency: "USD" }, "en"), "");
});

test("selection totals sum only numeric UZS rows and disclose exclusions", () => {
  assert.deepEqual(
    selectionTotal([
      { status: "numeric", amount: "96000", currency: "UZS" },
      { status: "numeric", amount: "221400", currency: "UZS" },
      { status: "on_request", amount: null, currency: null },
    ]),
    { total: "317400", excluded: true },
  );
  assert.deepEqual(
    selectionTotal([
      { status: "on_request", amount: null, currency: null },
      { status: "unavailable", amount: null, currency: null },
    ]),
    { total: null, excluded: true },
  );
  assert.deepEqual(
    selectionTotal([{ status: "numeric", amount: "1440", currency: "UZS" }]),
    { total: "1440", excluded: false },
  );
});
