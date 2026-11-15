import { filterItems, formatPercent, formatPrice, isIndex, sparklinePath, type Index, type Item } from "./logic.js";

const root = document.getElementById("app");
if (root === null) throw new Error("missing #app");
const app: HTMLElement = root;

async function getJson(path: string): Promise<unknown> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.json();
}

function el<K extends keyof HTMLElementTagNameMap>(
  tag: K, text?: string, cls?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (cls !== undefined) node.className = cls;
  return node;
}

function renderTable(index: Index, category: string | null, detail: HTMLElement): HTMLElement {
  const table = el("table");
  const head = el("tr");
  for (const h of ["Product", "Price", `P(drop ≥5% in ${index.horizon_days}d)`]) head.append(el("th", h));
  table.append(head);
  for (const item of filterItems(index.items, category)) {
    const row = el("tr");
    row.tabIndex = 0;
    row.append(el("td", item.name), el("td", formatPrice(item.price)));
    const cell = el("td");
    const bar = el("span", "", "bar");
    bar.style.width = `${Math.round(item.probability * 100)}%`;
    cell.append(bar, el("span", formatPercent(item.probability), "pct"));
    row.append(cell);
    const open = (): void => { void showDetail(item, detail); };
    row.addEventListener("click", open);
    row.addEventListener("keydown", (e) => { if (e.key === "Enter") open(); });
    table.append(row);
  }
  return table;
}

async function showDetail(item: Item, detail: HTMLElement): Promise<void> {
  const data = (await getJson(`data/items/${item.sku}.json`)) as { history: { day: string; price: number }[] };
  const prices = data.history.map((p) => p.price);
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 300 80");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", `Simulated price history for ${item.name}`);
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", sparklinePath(prices, 300, 80));
  svg.append(path);
  detail.replaceChildren(
    el("h2", item.name),
    el("p", `Simulated price history, last ${prices.length} days. ${formatPercent(item.probability)} simulated chance of a ≥5% drop.`),
    svg,
  );
}

async function main(): Promise<void> {
  const raw = await getJson("data/index.json");
  if (!isIndex(raw)) throw new Error("unexpected data format");
  const detail = el("section", undefined, "detail");
  const results = el("div");
  const tabs = el("nav");
  const show = (category: string | null): void => results.replaceChildren(renderTable(raw, category, detail));
  const mk = (label: string, cat: string | null): void => {
    const b = el("button", label);
    b.addEventListener("click", () => show(cat));
    tabs.append(b);
  };
  mk("All", null);
  for (const c of raw.categories) mk(c.name, c.id);
  const banner = el("p", `SIMULATED DATA — as of ${raw.as_of}. ${raw.disclaimer}`, "banner");
  app.replaceChildren(banner, tabs, results, detail);
  show(null);
}

main().catch((err: unknown) => {
  app.replaceChildren(el("p", `Failed to load simulated data: ${String(err)}`, "banner"));
});
