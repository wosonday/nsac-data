"""Tái lập run NASA-cl 2026-11-11 trên dữ liệu thật. Chạy: uv run pytest -m slow -v
(Ghi run mới vào data/ như chạy tay. Sleep đọc 20 file EDF, mất vài phút.)"""

from pathlib import Path

import pandas as pd
import pytest

from sky_ml._cli import main
from sky_ml._jsonio import read_json
from sky_ml._runs import resolve_run
from sky_ml._settings import load_settings

ROOT = Path(__file__).parents[1]
# task: (metric, {model: giá trị}, độ bao phủ khoảng 90% hoặc None, p hoán vị hoặc None, sai số cho phép)
# Nguồn: NASA-cl/reports/pipeline/<task>/2026-11-11_*/metrics.csv + summary.json
EXPECTED = {
    "hr": ("mae", {"ridge": 3.917428446642468, "lightgbm": 4.066026551813598, "last_value": 4.465221425659498},
           0.9003961516694963, None, 1e-6),
    "dose": ("mae", {"lightgbm": 0.7691257887059307, "ridge": 0.977819262439791, "last_value": 2.1366533006323554},
             0.8975547386926642, None, 1e-6),
    "cpet": ("mae", {"ridge": 2.83625335758478, "lightgbm": 3.3980908213149665, "mean_delta": 3.616899043503787,
                     "persistence": 4.12527450090909}, 0.9090909090909091, 0.004975124378109453, 1e-6),
    "sleep": ("macro_f1", {"lightgbm": 0.784290137538213, "logistic": 0.7598226825978867,
                           "majority": 0.11866152553661058}, None, None, 0.005),
}


@pytest.mark.slow
@pytest.mark.parametrize("task", sorted(EXPECTED))
def test_reproduce_2026_11_11(task):
    cfg = str(ROOT / "sky_ml.yaml")
    for step in ("build-features", "train", "evaluate"):
        main(["--config", cfg, step, task])
    run = resolve_run(load_settings(ROOT / "sky_ml.yaml"), task)
    metric, expected, coverage, p_value, tol = EXPECTED[task]
    metrics = pd.read_csv(run.models / "metrics.csv").set_index("model")
    for model, value in expected.items():
        assert metrics.loc[model, metric] == pytest.approx(value, abs=tol)
    summary = read_json(run.models / "summary.json")
    if coverage is not None:
        assert summary["interval_coverage"]["observed_coverage"] == pytest.approx(coverage, abs=1e-6)
    if p_value is not None:
        assert summary["permutation_test"]["p_value"] == pytest.approx(p_value, abs=1e-9)
