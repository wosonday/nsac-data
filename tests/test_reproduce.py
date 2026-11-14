"""Tái lập run NASA-cl 2026-11-11 trên dữ liệu thật. Chạy: uv run pytest -m slow -v"""
import json
from pathlib import Path

import pandas as pd
import pytest

from sky_ml.cli import main
from sky_ml.runs import resolve_run
from sky_ml.settings import load_settings

ROOT = Path(__file__).parents[1]
EXPECTED = {"hr": ({"ridge": 3.917428446642468, "lightgbm": 4.066026551813598, "last_value": 4.465221425659498},
                   0.9003961516694963)}


@pytest.mark.slow
@pytest.mark.parametrize("task", sorted(EXPECTED))
def test_reproduce_2026_11_11(task):
    cfg = str(ROOT / "sky_ml.yaml")
    for step in ("prepare", "train", "evaluate"):
        main(["--config", cfg, step, task])
    run = resolve_run(load_settings(ROOT / "sky_ml.yaml"), task)
    metrics = pd.read_csv(run / "metrics.csv").set_index("model")
    mae, coverage = EXPECTED[task]
    for model, value in mae.items():
        assert metrics.loc[model, "mae"] == pytest.approx(value, abs=1e-6)
    summary = json.loads((run / "summary.json").read_text())
    assert summary["interval_coverage"]["observed_coverage"] == pytest.approx(coverage, abs=1e-6)
