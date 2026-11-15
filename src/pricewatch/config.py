"""Load category configs from YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from pricewatch.domain import CategoryConfig


def load_categories(config_dir: Path) -> list[CategoryConfig]:
    configs = [
        CategoryConfig.model_validate(yaml.safe_load(p.read_text(encoding="utf-8")))
        for p in sorted(config_dir.glob("*.yaml"))
    ]
    ids = [c.id for c in configs]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate category ids")
    return configs
