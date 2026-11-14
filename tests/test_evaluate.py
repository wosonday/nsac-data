import math

import pandas as pd

from sky_ml.evaluate import evaluate, interval_half_width


def test_half_width_infinite_when_too_few():
    assert interval_half_width([1.0] * 8, 0.10) == math.inf      # k = ceil(9*0.9)=9 > 8


def test_half_width_order_statistic():
    assert interval_half_width(list(range(1, 20)), 0.10) == 18.0  # n=19 → k=18


def test_evaluate_sorts_best_first_and_diff_vs_baseline():
    rows = []
    for fold in ["a", "b", "c"]:
        rows += [{"fold": fold, "row": 0, "subject_id": fold, "model": "base", "y_true": 10, "y_pred": 12},
                 {"fold": fold, "row": 0, "subject_id": fold, "model": "good", "y_true": 10, "y_pred": 11}]
    m = evaluate(pd.DataFrame(rows), {"kind": "regression", "baseline": "base", "bootstrap_samples": 200})
    assert list(m.model) == ["good", "base"] and m.loc[0, "diff_vs_baseline"] == -1.0
