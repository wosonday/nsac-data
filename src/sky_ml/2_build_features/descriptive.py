"""Bảng MÔ TẢ (không train mô hình) cho dữ liệu thật quá ít người / không có persona / lấy mẫu rời rạc.

- osd_labs   : Inspiration4 (OSD-569 CBC, OSD-575 CMP + 2 panel Eve) — 4 phi hành gia THẬT, 7 mốc L-92 … R+194.
               Bảng dài: crew, timepoint, ngày tương đối với phóng/hạ cánh, analyte, value, unit, range_min/max, out_of_range.
- cortisol   : UTMB Campaign 3 (BRSMLVR) cortisol nước bọt — trung bình theo người × ngày nghiên cứu.
               (File C3F "Saliva_Cortisol" của nguồn thực chứa cột VZV → bị bỏ qua.)
- dxa_regional: UTMB CFT70 BRSMiDXA (5 người, không có persona) — BMD hông/cột sống theo NGÀY quét, % so với lần quét đầu.
Khoảng tham chiếu nguồn KHÔNG phải ngưỡng cảnh báo cho phi hành gia; cột out_of_range chỉ để mô tả.
"""
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from .cpet import _verified_csv

_VALUE = re.compile(r"^(?P<analyte>.+?)_(?:value|concentration)_(?P<unit>.+)$")


def _timepoint_day(tp: pd.Series) -> pd.Series:
    """L-3 → −3 (trước phóng), R+45 → +45 (sau hạ cánh; chuyến bay 3 ngày nên R+0 ≈ ngày 3 sau phóng)."""
    m = tp.str.extract(r"^(?P<k>[LR])(?P<d>[+-]\d+)$")
    return pd.to_numeric(m.d, errors="coerce")


def osd_labs(data_dir: Path, files: list[str]) -> pd.DataFrame:
    parts = []
    for rel in files:
        wide = pd.read_csv(data_dir / rel, encoding="utf-8-sig")
        sample = wide["Sample Name"].str.extract(r"^(?P<crew>C\d{3})_(?P<matrix>[A-Za-z-]+)_(?P<tp>[LR][+-]\d+)(?:_\w+)?$")
        for col in wide.columns:
            m = _VALUE.match(col)
            if not m:
                continue
            a, unit = m["analyte"], m["unit"]
            lo = wide.get(f"{a}_range_min_{unit}")
            hi = wide.get(f"{a}_range_max_{unit}")
            frame = pd.DataFrame({"panel": Path(rel).stem.split("_TRANSFORMED")[0], "crew": "i4:" + sample.crew,
                                  "timepoint": sample.tp, "phase": np.where(sample.tp.str.startswith("L"), "PRE_FLIGHT", "POST_FLIGHT"),
                                  "relative_day": _timepoint_day(sample.tp), "analyte": a, "unit": unit,
                                  "value": pd.to_numeric(wide[col], errors="coerce"),
                                  "range_min": pd.to_numeric(lo, errors="coerce") if lo is not None else np.nan,
                                  "range_max": pd.to_numeric(hi, errors="coerce") if hi is not None else np.nan})
            parts.append(frame)
    t = pd.concat(parts, ignore_index=True).dropna(subset=["value"])
    t["out_of_range"] = ((t.value < t.range_min) | (t.value > t.range_max)).where(t.range_min.notna() | t.range_max.notna())
    return t.rename(columns={"crew": "subject_id"}).sort_values(["panel", "analyte", "subject_id", "relative_day"]).reset_index(drop=True)


def cortisol(nlsp: Path, manifest: pd.DataFrame) -> pd.DataFrame:
    parts = []
    with zipfile.ZipFile(nlsp / "BRSMLVR.zip") as zf:
        for m in sorted(x for x in zf.namelist() if "ortisol" in x and x.endswith(".csv")):
            d = _verified_csv(zf, manifest, "BRSMLVR.zip", m)
            val = next((c for c in d.columns if "ortisol" in c), None)  # tên cột khác nhau giữa các file
            if val is None:     # vd. file C3F "Saliva_Cortisol" thực chứa cột VZV → bỏ, không đoán
                continue
            day = next(c for c in d.columns if "day" in c.lower())
            parts.append(pd.DataFrame({"subject_id": "utmb_c3:" + d.Subject.astype(str), "study_day": pd.to_numeric(d[day], errors="coerce"),
                                       "cortisol": pd.to_numeric(d[val], errors="coerce")}))
    f = pd.concat(parts).dropna()
    return (f.groupby(["subject_id", "study_day"]).cortisol.agg(["mean", "count"]).reset_index()
            .rename(columns={"mean": "cortisol_mean", "count": "n_samples"}))


def dxa_regional(nlsp: Path, manifest: pd.DataFrame) -> pd.DataFrame:
    cols = {"L_Hip": "Tot_BMD", "R_Hip": "Tot_BMD", "S_bone": "L14_BMD"}
    parts = []
    with zipfile.ZipFile(nlsp / "BRSMiDXA.zip") as zf:
        for m in sorted(x for x in zf.namelist() if x.endswith(".csv")):
            region = next((r for r in cols if f"_{r}_" in m), None)
            if region is None:
                continue
            d = _verified_csv(zf, manifest, "BRSMiDXA.zip", m)
            parts.append(pd.DataFrame({"subject_id": "utmb_cft70:" + d.Subject.astype(str), "region": region,
                                       "scan_date": pd.to_datetime(d.acq_time).dt.date,
                                       "bmd": pd.to_numeric(d[cols[region]], errors="coerce")}))
    f = pd.concat(parts).dropna().groupby(["subject_id", "region", "scan_date"]).bmd.mean().reset_index()
    first = f.groupby(["subject_id", "region"]).scan_date.transform("min")
    f["days_since_first_scan"] = (pd.to_datetime(f.scan_date) - pd.to_datetime(first)).dt.days
    base = f[f.days_since_first_scan.eq(0)].set_index(["subject_id", "region"]).bmd
    f["pct_vs_first_scan"] = 100 * (f.bmd / [base[(s, r)] for s, r in zip(f.subject_id, f.region)] - 1)
    return f.drop(columns="scan_date")


def build_descriptive(data_dir: Path, cfg: dict) -> tuple[pd.DataFrame, list[str]]:
    nlsp = data_dir / "raw/nlsp"
    kind = cfg["table"]
    if kind == "osd_labs":
        return osd_labs(data_dir, [p for p in cfg["inputs"] if p.endswith(".csv")]), []
    manifest = pd.read_csv(nlsp / "download_manifest.csv", keep_default_na=False)
    if kind == "cortisol":
        return cortisol(nlsp, manifest), []
    if kind == "dxa_regional":
        return dxa_regional(nlsp, manifest), []
    raise ValueError(f"table không hỗ trợ: {kind}")
