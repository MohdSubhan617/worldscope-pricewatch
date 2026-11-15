"""Build the daily digest (markdown) from the exported JSON. Everything is labelled simulated."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def build_digest(index: dict[str, Any], metrics: dict[str, Any], run_url: str | None = None) -> str:
    items = sorted(index["items"], key=lambda i: (-i["probability"], i["sku"]))
    high = sum(1 for i in items if i["probability"] >= 0.5)
    lines = [
        f"### Simulated day {index['as_of']}",
        "",
        "> **SIMULATED DATA.** Fictional products and prices from a seeded simulator; not real "
        "market data and not financial advice.",
        "",
        f"- Items: {len(items)}; at or above 50% simulated chance of a >=5% drop within "
        f"{index['horizon_days']} days: {high}",
        f"- Held-out Brier {metrics['brier']:.4f} (base rate {metrics['base_rate_brier']:.4f}), "
        f"ECE {metrics['ece']:.4f}",
        "",
        "| Product | Simulated price | P(drop) |",
        "|---|---|---|",
    ]
    for i in items[:5]:
        lines.append(f"| {i['name']} | ${i['price']:.2f} (sim) | {i['probability']:.0%} |")
    if run_url:
        lines += ["", f"[workflow run]({run_url})"]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    public = Path(argv[1])
    run_url = argv[2] if len(argv) > 2 else None
    index = json.loads((public / "index.json").read_text(encoding="utf-8"))
    metrics = json.loads((public / "metrics.json").read_text(encoding="utf-8"))
    sys.stdout.write(build_digest(index, metrics, run_url))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
