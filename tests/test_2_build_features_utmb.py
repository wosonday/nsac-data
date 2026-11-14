"""vitals / mood / glucose (UTMB) + dữ liệu giả định: các quy tắc làm sạch và tính tái lập."""
import importlib

import numpy as np
import pandas as pd

from sky_ml import _synthetic

vitals = importlib.import_module("sky_ml.2_build_features.vitals")
nnx = importlib.import_module("sky_ml.2_build_features.cft70_nnx")


def test_vitals_column_aliases_and_technical_range():
    a = pd.DataFrame({"Subject": ["7"], "Date": ["1/2/2007"], "Test_Phase": ["IN_TEST"], "BR_Day": ["1"],
                      "SysBP (mmHg)": ["300"], "DiaBP (mmHg)": ["70"], "Body Temp (Celsius)": ["36.6"], "Pulse (bpm)": ["60"]})
    b = pd.DataFrame({"Subject": ["C1G0001"], "Date": ["1/2/2004"], "Test_Phase": ["IN_TEST"], "BR_Day": ["1"],
                      "Blood Pressure, systolic": ["118"], "Blood Pressure, diastolic": ["NA"]})
    na, nb = vitals.normalize(a, "campaign_3"), vitals.normalize(b, "campaign_1")
    assert np.isnan(na.sbp[0]) and na.dbp[0] == 70 and na.temp[0] == 36.6     # 300 mmHg ngoài ngưỡng kỹ thuật
    assert nb.subject_id[0] == "utmb_c1:C1G0001" and nb.sbp[0] == 118 and np.isnan(nb.temp[0])


def test_vitals_conflicting_same_day_dropped():
    d = pd.DataFrame({"subject_id": ["s"] * 2, "cohort": "c", "date": pd.to_datetime(["2007-01-02"] * 2),
                      "phase": "IN", "br_day": 1.0, "sbp": [110.0, 130.0], "dbp": [70.0, 70.0], "temp": [36.5, np.nan],
                      "pulse": [60.0, 60.0]})
    one = vitals._dedupe(d).iloc[0]
    assert np.isnan(one.sbp) and one.dbp == 70 and one.temp == 36.5


def test_study_day_ordering():
    days = nnx._study_day(pd.Series(["PRE-TEST", "IN_TEST", "POST_TEST"]), pd.Series(["13", "3", "12"]))
    assert list(days) == [-13, 3, 82]


def test_glucose_target_is_change_from_pre_mean():
    o = pd.DataFrame({"subject_id": "p", "phase": ["PRE_TEST", "PRE_TEST", "PRE_TEST", "IN_TEST"],
                      "study_day": [-20, -1, -1, 66], "minute": [0, 0, 120, 0],
                      "glucose": [88.0, 92.0, 110.0, 95.0], "insulin": [5.0, 7.0, 30.0, 6.0]})
    row = nnx.glucose_table(o, 66).iloc[0]
    assert row.pre_glucose_0 == 90 and row.pre_glucose_120 == 110 and row.delta_glucose_0 == 5


def test_synthetic_components_and_reproducible():
    rng = np.random.default_rng(0)
    real = pd.DataFrame({"subject_id": np.repeat(list("abcd"), 10), "t": np.tile(np.arange(10), 4),
                         "v": rng.normal(50, 5, 40)})
    comp = _synthetic._components(real, "v", "t")
    assert comp["n_people"] == 4 and 0 <= comp["rho"] <= 0.95 and comp["sigma_within"] > 0
    y1 = _synthetic._simulate(np.arange(10.0), comp, np.random.default_rng(17))
    y2 = _synthetic._simulate(np.arange(10.0), comp, np.random.default_rng(17))
    assert np.array_equal(y1, y2)                       # seed cố định → tái lập


def test_synthetic_never_listed_as_training_input():
    from pathlib import Path

    import yaml
    tasks = yaml.safe_load((Path(__file__).parents[1] / "configs/tasks.yaml").read_text(encoding="utf-8"))
    assert not any("synthetic" in str(t.get("inputs", "")) for t in tasks.values())
