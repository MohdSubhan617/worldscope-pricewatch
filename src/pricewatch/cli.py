"""Command line entry point: `pricewatch run`."""

from __future__ import annotations

import argparse
from pathlib import Path

from pricewatch.backtest import render_markdown, timed_backtest
from pricewatch.clock import initial_day
from pricewatch.pipeline import labelled_features, run
from pricewatch.retrain import retrain
from pricewatch.settings import Settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pricewatch", description="Simulated price-drop odds")
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="advance one simulated day and export JSON")
    r.add_argument("--out", type=Path, default=Path("work/out"))
    r.add_argument("--no-advance", action="store_true", help="do not advance the clock")
    b = sub.add_parser("backtest", help="rolling-origin backtest; writes a markdown report")
    b.add_argument("--out", type=Path, default=Path("BENCHMARKS.md"))
    b.add_argument("--embargo", type=int, default=7)
    t = sub.add_parser("retrain", help="fit a challenger and promote it only by policy")
    t.add_argument("--state", type=Path, default=None, help="state dir (default: data_dir)")
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    if args.command == "retrain":
        report = retrain(settings, args.state or settings.data_dir)
        print(f"retrain {report.as_of}: {report.action}")  # noqa: T201
        if report.decision is not None:
            print(f"  {report.decision.reason}")  # noqa: T201
        drifted = [r.column for r in report.drift if r.drifted]
        print(f"  drifted features: {drifted or 'none'}")  # noqa: T201
        return 0
    if args.command == "backtest":
        labelled = labelled_features(settings, initial_day(settings))
        seed, horizon = settings.seed, settings.horizon_days
        results, elapsed = timed_backtest(labelled, seed, horizon, args.embargo)
        text = render_markdown(results, seed, horizon, args.embargo, elapsed)
        args.out.write_text(text, encoding="utf-8", newline="\n")
        print(f"backtest: {len(results)} folds in {elapsed:.1f}s -> {args.out}")  # noqa: T201
        return 0
    today = run(settings, args.out, advance=not args.no_advance)
    print(f"simulated day {today} exported to {args.out}")  # noqa: T201
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
