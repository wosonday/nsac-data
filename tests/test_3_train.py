import numpy as np
import pandas as pd

from sky_ml._steps import train

make_folds, train_predict = train.make_folds, train.train_predict

CFG = {"kind": "regression", "target": "y", "seed": 17, "split": {"type": "leave_one_subject_out"},
       "models": {"last_value": {"class": "sky_ml._models.LastValue"},
                  "ridge": {"class": "sklearn.linear_model.Ridge", "params": {"alpha": 1.0}, "scale": True}}}


def _table():
    rng = np.random.default_rng(0)
    subj = np.repeat(["a", "b", "c"], 10)
    x = rng.normal(70, 5, 30)
    return pd.DataFrame({"subject_id": subj, "last_value": x, "y": x + rng.normal(0, 1, 30)})


def test_loso_holds_out_whole_subject():
    t = _table()
    for f in make_folds(t, CFG["split"]):
        assert set(t.loc[f["test"], "subject_id"]) == {f["name"]}
        assert f["name"] not in set(t.loc[f["train"], "subject_id"])


def test_by_month_respects_gap():
    times = pd.date_range("2022-01-01", "2022-06-30", freq="D")
    t = pd.DataFrame({"subject_id": "dev", "cutoff_time": times})
    for f in make_folds(t, {"type": "by_month", "test_months": [4, 5], "gap_days": 1}):
        first_test = t.loc[f["test"], "cutoff_time"].min()
        assert t.loc[f["train"], "cutoff_time"].max() < first_test - pd.Timedelta(days=1)


def test_oof_has_one_row_per_test_row_per_model():
    oof = train_predict(_table(), ["last_value"], CFG)
    assert len(oof) == 30 * 2 and set(oof.model) == {"last_value", "ridge"}
    assert oof.groupby("model").row.nunique().eq(30).all()
