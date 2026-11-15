import json
from datetime import timedelta
from pathlib import Path

import pytest
from tools.check_simulated import check

from pricewatch.clock import initial_day
from pricewatch.pipeline import run
from pricewatch.settings import Settings

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.slow
def test_run_exports_simulated_json_and_advances_clock(tmp_path: Path) -> None:
    s = Settings(data_dir=tmp_path / "data", config_dir=ROOT / "configs" / "categories")
    out = tmp_path / "out"
    today = run(s, out)
    assert today == initial_day(s) + timedelta(days=1)
    assert check(out) == []
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert index["items"]
    assert all(0 <= i["probability"] <= 1 for i in index["items"])
    assert "simulated" in index["disclaimer"].lower()
    assert run(s, out) == today + timedelta(days=1)


def test_check_flags_unmarked_json(tmp_path: Path) -> None:
    (tmp_path / "a.json").write_text('{"x": 1}', encoding="utf-8")
    assert check(tmp_path) == [str(tmp_path / "a.json")]
