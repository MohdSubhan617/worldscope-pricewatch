"""Command line entry point: `pricewatch run`."""

from __future__ import annotations

import argparse
from pathlib import Path

from pricewatch.pipeline import run
from pricewatch.settings import Settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pricewatch", description="Simulated price-drop odds")
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="advance one simulated day and export JSON")
    r.add_argument("--out", type=Path, default=Path("work/out"))
    r.add_argument("--no-advance", action="store_true", help="do not advance the clock")
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    today = run(settings, args.out, advance=not args.no_advance)
    print(f"simulated day {today} exported to {args.out}")  # noqa: T201
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
