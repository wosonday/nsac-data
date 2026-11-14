"""UTMB bed rest – CRF Daily Vitals → giá trị NGÀY TỚI (huyết áp tâm thu/tâm trương, nhiệt độ) từ `past` ngày trước.

Ba cohort trong CRF.zip, KHÔNG gộp người giữa các cohort:
- campaign_3 : 23 người → dùng để TRAIN (LOSO).
- cft70      : 5160, 8072, 8936 → kiểm tra NGOÀI cohort (3 persona ayla, dae-jung, lena).
- campaign_1 : C1G0001–3       → kiểm tra NGOÀI cohort (3 persona tomas, yuki, noor).
Mỗi file có tên cột khác nhau (12 kiểu) → chuẩn hóa theo COLUMN_ALIASES. Kiểm SHA-256 + MD5 từng member.
Ngưỡng VALID_RANGE là ngưỡng KỸ THUẬT để loại số ghi hỏng, không phải ngưỡng lâm sàng.
Cùng người, cùng ngày, giá trị khác nhau → bỏ cả ngày (không đoán bản nào đúng).
"""
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from .cpet import _verified_csv
from .windows import check_features, latest_window, make_windows

COLUMN_ALIASES = {
    "sbp": ["SysBP", "SysBP (mmHg)", "Blood Pressure, systolic"],
    "dbp": ["DiaBP", "DiaBP (mmHg)", "Blood Pressure, diastolic"],
    "temp": ["Body Temp", "Body Temp (Celsius)", "Temperature, body (Celsius)"],
    "pulse": ["Pulse", "Pulse (bpm)"],
    "date": ["Date", "Test_Date"],
}
VALID_RANGE = {"sbp": (60, 250), "dbp": (30, 150), "temp": (34.0, 42.0), "pulse": (30, 220)}
UNITS = {"sbp": "mmHg", "dbp": "mmHg", "temp": "°C", "pulse": "bpm"}
COHORTS = {"campaign_3": ("campaign_3/CRF_Campaign_3_Daily_Vitals/", "utmb_c3:"),
           "cft70": ("cft70/CRF_CFT70_VITALS/", "utmb_cft70:"),
           "campaign_1": ("campaign_1/CRF_Campaign_1_Daily_Vitals/CRF_Campaign_1_Daily_Vitals_All.csv", "utmb_c1:")}


def _pick(frame: pd.DataFrame, name: str) -> pd.Series:
    for alias in COLUMN_ALIASES[name]:
        if alias in frame:
            return frame[alias]
    return pd.Series(np.nan, index=frame.index)


def normalize(frame: pd.DataFrame, cohort: str) -> pd.DataFrame:
    """Một file nguồn → subject_id, cohort, date, phase, br_day, sbp, dbp, temp, pulse (ngoài ngưỡng → NaN)."""
    out = pd.DataFrame({"subject_id": COHORTS[cohort][1] + frame.Subject.astype(str).str.strip(),
                        "cohort": cohort,
                        "date": pd.to_datetime(_pick(frame, "date"), format="%m/%d/%Y", errors="coerce"),
                        "phase": frame.Test_Phase, "br_day": pd.to_numeric(frame.BR_Day, errors="coerce")})
    for m, (lo, hi) in VALID_RANGE.items():
        v = pd.to_numeric(_pick(frame, m), errors="coerce")
        out[m] = v.where(v.between(lo, hi))
    return out.dropna(subset=["date"])


def _dedupe(days: pd.DataFrame) -> pd.DataFrame:
    """Trùng người-ngày: giữ giá trị nếu mọi bản ghi giống nhau, ngược lại NaN."""
    def one(s):
        u = s.dropna().unique()
        return u[0] if len(u) == 1 else np.nan
    keys = ["subject_id", "cohort", "date"]
    first = days.groupby(keys, as_index=False)[["phase", "br_day"]].first()
    vals = days.groupby(keys)[list(VALID_RANGE)].agg(one).reset_index()
    return first.merge(vals, on=keys)


def read_vitals(nlsp: Path, cohorts: list[str]) -> pd.DataFrame:
    manifest = pd.read_csv(nlsp / "download_manifest.csv", keep_default_na=False)
    parts = []
    with zipfile.ZipFile(nlsp / "CRF.zip") as zf:
        for cohort in cohorts:
            prefix = COHORTS[cohort][0]
            members = [m for m in zf.namelist() if m.startswith(prefix) and m.endswith(".csv")]
            parts += [normalize(_verified_csv(zf, manifest, "CRF.zip", m), cohort) for m in sorted(members)]
    return _dedupe(pd.concat(parts, ignore_index=True)).sort_values(["subject_id", "date"]).reset_index(drop=True)


def _grids(days: pd.DataFrame, measure: str):
    for sid, g in days.groupby("subject_id"):
        grid = pd.date_range(g.date.min(), g.date.max(), freq="D")
        yield sid, g.set_index("date")[measure].reindex(grid).to_numpy(float), grid


def vitals_windows(days: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    w, names, parts = cfg["window"], check_features(cfg["features"]), []
    for sid, grid, dates in _grids(days, cfg["measure"]):
        t = make_windows(grid, dates, w["past"], w["future"], w["step"], names)
        if len(t):
            t.insert(0, "subject_id", sid)
            parts.append(t)
    cols = ["subject_id", "cutoff_time", *names, "target"]
    t = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=cols)
    return t.rename(columns={"target": cfg["target"]})


def vitals_latest(days: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    names = check_features(cfg["features"])
    return pd.DataFrame([{"subject_id": s, **latest_window(g, d, cfg["window"]["past"], names)}
                         for s, g, d in _grids(days, cfg["measure"])])


def build_vitals(data_dir: Path, cfg: dict) -> tuple[pd.DataFrame, list[str]]:
    if cfg["measure"] not in UNITS:
        raise ValueError(f"measure phải là một trong {list(UNITS)}")
    nlsp = data_dir / "raw/nlsp"
    table = vitals_windows(read_vitals(nlsp, [cfg["train_cohort"]]), cfg)
    external = cfg.get("external_cohorts", [])
    if external:   # bảng NGOÀI cohort: cùng quy tắc, KHÔNG dùng để train; bước evaluate chấm điểm riêng
        table.attrs["external"] = vitals_windows(read_vitals(nlsp, external), cfg)
    return table, check_features(cfg["features"])


