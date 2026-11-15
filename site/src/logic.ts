export interface Item {
  sku: string;
  category: string;
  brand: string;
  name: string;
  as_of: string;
  price: number;
  probability: number;
}

export interface Index {
  simulated: true;
  disclaimer: string;
  as_of: string;
  horizon_days: number;
  categories: { id: string; name: string }[];
  items: Item[];
}

export function isIndex(value: unknown): value is Index {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return v["simulated"] === true && Array.isArray(v["items"]) && Array.isArray(v["categories"]);
}

export function filterItems(items: readonly Item[], category: string | null): Item[] {
  const rows = category === null ? [...items] : items.filter((i) => i.category === category);
  return rows.sort((a, b) => b.probability - a.probability || a.sku.localeCompare(b.sku));
}

export function formatPercent(p: number): string {
  return `${(p * 100).toFixed(0)}%`;
}

export function formatPrice(p: number): string {
  return `$${p.toFixed(2)} (sim)`;
}

export function sparklinePath(values: readonly number[], w: number, h: number): string {
  if (values.length < 2) return "";
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * w;
      const y = h - ((v - min) / span) * h;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}
