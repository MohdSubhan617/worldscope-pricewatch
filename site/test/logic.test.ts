import assert from "node:assert/strict";
import { test } from "node:test";
import { filterItems, formatPercent, formatPrice, isIndex, sparklinePath, type Item } from "../src/logic.js";

const mk = (sku: string, category: string, probability: number): Item => ({
  sku, category, brand: "b", name: sku, as_of: "2026-01-01", price: 10, probability,
});

test("filterItems sorts by probability desc and filters category", () => {
  const items = [mk("a", "x", 0.2), mk("b", "y", 0.9), mk("c", "x", 0.5)];
  assert.deepEqual(filterItems(items, "x").map((i) => i.sku), ["c", "a"]);
  assert.equal(filterItems(items, null)[0]?.sku, "b");
});

test("formatting always labels prices as simulated", () => {
  assert.equal(formatPercent(0.256), "26%");
  assert.match(formatPrice(5), /sim/);
});

test("isIndex requires the simulated flag", () => {
  assert.equal(isIndex({ simulated: true, items: [], categories: [] }), true);
  assert.equal(isIndex({ simulated: false, items: [], categories: [] }), false);
});

test("sparklinePath handles short and flat series", () => {
  assert.equal(sparklinePath([1], 10, 10), "");
  assert.match(sparklinePath([2, 2, 2], 10, 10), /^M0\.0,10\.0 L5\.0,10\.0 L10\.0,10\.0$/);
});
