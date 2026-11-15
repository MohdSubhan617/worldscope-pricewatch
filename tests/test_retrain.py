import json
from pathlib import Path

import pytest

from pricewatch.retrain import load_champion, retrain
from pricewatch.settings import Settings

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.slow
def test_first_retrain_promotes_then_identical_challenger_is_kept_out(tmp_path: Path) -> None:
    s = Settings(
        data_dir=tmp_path,
        config_dir=ROOT / "configs" / "categories",
        calendar_path=ROOT / "configs" / "sale_calendar.yaml",
    )
    first = retrain(s, tmp_path, n_boot=300)
    assert first.action == "promoted-initial"
    champ = load_champion(tmp_path / "models")
    assert champ is not None
    second = retrain(s, tmp_path, n_boot=300)
    assert second.action == "kept-champion"  # same data, same seed: no reliable improvement
    assert second.decision is not None
    assert not second.decision.promote
    report = json.loads((tmp_path / "models" / "last_retrain.json").read_text(encoding="utf-8"))
    assert report["simulated"] is True
    assert "SIMULATED" in report["disclaimer"]
