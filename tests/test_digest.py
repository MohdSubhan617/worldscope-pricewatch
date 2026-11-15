import json
from pathlib import Path

import pytest
from tools.digest import build_digest, main

INDEX = {
    "simulated": True,
    "as_of": "2026-11-02",
    "horizon_days": 14,
    "items": [
        {"sku": f"s{i}", "name": f"Item {i}", "price": 10.0 + i, "probability": i / 10}
        for i in range(8)
    ],
}
METRICS = {"brier": 0.09, "base_rate_brier": 0.2, "ece": 0.01}


def test_digest_is_labelled_simulated_and_lists_top_five() -> None:
    text = build_digest(INDEX, METRICS, "https://example.invalid/run/1")
    assert "SIMULATED DATA" in text
    assert text.count("(sim)") == 5
    assert "Item 7" in text
    assert "Item 2" not in text  # only the top five by probability
    assert "workflow run" in text
    assert "at or above 50% simulated chance of a >=5% drop within 14 days: 3" in text


def test_main_reads_exported_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "index.json").write_text(json.dumps(INDEX), encoding="utf-8")
    (tmp_path / "metrics.json").write_text(json.dumps(METRICS), encoding="utf-8")
    assert main(["digest", str(tmp_path)]) == 0
    assert "Simulated day 2026-11-02" in capsys.readouterr().out
