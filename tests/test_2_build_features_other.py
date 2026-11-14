"""Bước 2 cho dose / cpet / sleep: kiểm các quy tắc làm sạch quan trọng trên dữ liệu giả nhỏ."""
import importlib

import numpy as np
import pandas as pd
import pytest

dose = importlib.import_module("sky_ml.2_build_features.dose")
cpet = importlib.import_module("sky_ml.2_build_features.cpet")
sleep = importlib.import_module("sky_ml.2_build_features.sleep")
DOSE_CFG = {"window": {"past": 6, "future": 2, "step": 2}, "target": "dose_rate_next_1h",
            "features": ["last_value", "mean_all"]}


def _lidal(n=40):
    t = pd.date_range("2022-04-01", periods=n, freq="5min")
    return pd.DataFrame({"timestamp": t.astype(str), "absorbed_dose_rate": np.arange(n, dtype=float)})


def test_dose_conflicting_timestamp_dropped_not_guessed():
    raw = _lidal()
    raw = pd.concat([raw, pd.DataFrame({"timestamp": [raw.timestamp[10]], "absorbed_dose_rate": [999.0]})])
    table = dose.dose_windows(raw, DOSE_CFG)
    assert 999.0 not in table.values
    assert not ((pd.to_datetime(table.cutoff_time) >= pd.Timestamp(raw.timestamp[10]))
                & (pd.to_datetime(table.cutoff_time) < pd.Timestamp(raw.timestamp[10]) + pd.Timedelta("30min"))).any()


def test_dose_target_is_future_mean_only():
    table = dose.dose_windows(_lidal(), DOSE_CFG)
    first = table.iloc[0]
    assert first.last_value == 5.0 and first.dose_rate_next_1h == 6.5      # mean(6, 7): chỉ tương lai


def test_dose_latest_uses_last_measured_point():
    row = dose.dose_latest(_lidal(), DOSE_CFG).iloc[0]
    assert row.last_value == 39.0 and row.subject_id == dose.SUBJECT


def _visit(sid, visit, group, rel=40.0, hrpk=180.0, date="01/01/2020"):
    return {"SUBJECT": sid, "visit": visit, "GROUP": group, "REL VO2PK": rel, "VO2PK": rel * 80 / 1000,
            "WEIGHT": 80.0, "HRPK": hrpk, "AGE": 35, "BR DAY": 1, "DATE": date}


def test_cpet_qc_and_group_rules():
    frame = pd.DataFrame([_visit(1, "PRE", "EXERCISE + TESTOSTERONE"), _visit(1, "POST1", "EXERCISE", 36, date="03/15/2020"),
                          _visit(2, "PRE", "CONTROL", hrpk=15), _visit(2, "POST1", "CONTROL", date="03/15/2020"),
                          _visit(3, "PRE", "EXERCISE"), _visit(3, "POST1", "EXERCISE", date="03/15/2020")])
    refs = {"1": {"MR079G": "EXERCISE"}, "2": {"MR079G": "CONTROL"}, "3": {"MR079G": "CONTROL"}}
    task = cpet.build_task(cpet.canonicalize(frame, refs)).set_index("subject_id")
    assert task.loc["utmb_cft70:1"].eligible and task.loc["utmb_cft70:1"].delta_vo2 == pytest.approx(-4.0)
    assert "PRE_cpet_qc" in task.loc["utmb_cft70:2"].exclusion_reason          # HRPK < 20
    assert "PRE_group_unresolved" in task.loc["utmb_cft70:3"].exclusion_reason  # nhãn mâu thuẫn → không đoán
    table = cpet.cpet_table(task.reset_index())
    assert list(table.subject_id) == ["utmb_cft70:1"] and table.group_EXERCISE[0] == 1.0


def test_sleep_band_powers_shape_and_dominant_band():
    fs, t = 100.0, np.arange(3000) / 100.0
    segments = np.stack([np.sin(2 * np.pi * 2 * t), np.sin(2 * np.pi * 10 * t)])   # 2 Hz (delta), 10 Hz (alpha)
    p = sleep.band_powers(segments, fs)
    assert set(p) == {"logpow", *sleep.BANDS}
    assert p["delta"][0] > p["alpha"][0] and p["alpha"][1] > p["delta"][1]
