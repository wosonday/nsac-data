import math

import numpy as np
import pandas as pd

from sky_ml._models import build_model
from sky_ml._steps import build_features, predict

FEATS = ["last_value"]
CFG = {"target": "y", "unit": "bpm"}


def _setup():
    train = pd.DataFrame({"subject_id": ["a"] * 5 + ["b"] * 5, "last_value": np.linspace(60, 100, 10)})
    train["y"] = train.last_value + 1
    model = build_model({"class": "sklearn.linear_model.Ridge", "params": {"alpha": 1.0}, "scale": True}, 17)
    return train, model.fit(train[FEATS], train.y)


def test_predicts_with_interval_for_new_person():
    train, model = _setup()
    rows = pd.DataFrame({"subject_id": ["new"], "cutoff_time": [1], "last_value": [80.0]})
    out = predict.predict_rows(model, rows, FEATS, 5.0, train, CFG, "ridge")
    assert not out.abstain[0] and not out.in_sample[0]
    assert out.high90[0] - out.low90[0] == 10.0


def test_abstains_on_missing_and_out_of_range():
    train, model = _setup()
    rows = pd.DataFrame({"subject_id": ["n1", "n2"], "cutoff_time": [1, 1], "last_value": [np.nan, 250.0]})
    out = predict.predict_rows(model, rows, FEATS, 5.0, train, CFG, "ridge")
    assert out.abstain.all() and out.prediction.isna().all()
    assert list(out.reasons) == ["missing_features", "out_of_training_range"]


def test_flags_in_sample_and_infinite_interval():
    train, model = _setup()
    rows = pd.DataFrame({"subject_id": ["a"], "cutoff_time": [1], "last_value": [70.0]})
    out = predict.predict_rows(model, rows, FEATS, math.inf, train, CFG, "ridge")
    assert out.in_sample[0] and "insufficient_calibration_data" in out.reasons[0]


def test_latest_window_uses_only_last_points():
    row = build_features.windows.latest_window(np.arange(40, dtype=float), np.arange(100, 140), past=30, names=["last_value", "min_all"])
    assert row["last_value"] == 39 and row["cutoff_time"] == 139 and row["min_all"] == 10


def test_latest_window_with_gap_gives_nan():
    v = np.arange(40, dtype=float)
    v[-3] = np.nan
    assert math.isnan(build_features.windows.latest_window(v, np.arange(40), 30, ["mean_all"])["mean_all"])


def test_classification_returns_label_and_probabilities():
    from sklearn.dummy import DummyClassifier

    train = pd.DataFrame({"subject_id": ["a"] * 4, "x": [0.0, 1, 2, 3], "stage": ["W", "N2", "N2", "REM"]})
    model = DummyClassifier(strategy="prior").fit(train[["x"]], train.stage)
    cfg = {"kind": "classification", "classes": ["W", "N1", "N2", "N3", "REM"], "target": "stage", "unit": None}
    rows = pd.DataFrame({"subject_id": ["new"], "x": [1.5]})
    out = predict.predict_rows(model, rows, ["x"], float("nan"), train, cfg, "majority")
    assert out.prediction[0] == "N2" and out.p_N2[0] == 0.5 and out.p_N1[0] == 0.0
    assert not out.abstain[0] and "low90" not in out

