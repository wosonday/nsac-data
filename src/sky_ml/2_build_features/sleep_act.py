"""UTMB Bed Rest Campaign 1 – actigraphy cổ tay (BRSMAct) → chỉ số giấc ngủ của ĐÊM TỚI từ `past` đêm trước.

3 người (C1G0001–3), nằm giường ~60 ngày, mỗi đêm một hàng: độ trễ vào giấc, thời lượng ngủ, hiệu suất ngủ.
Kiểm SHA-256 + MD5 của member ZIP theo raw/nlsp/download_manifest.csv (dùng chung với cpet).
Đêm thiếu ("No Data") = NaN; cửa sổ chạm NaN bị bỏ, không nội suy. Ghi chú thuốc ngủ (vd. "Ambien") giữ ở cột `sedative`.
"""
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from .cpet import _verified_csv
from .windows import check_features, latest_window, make_windows

MEMBER = "campaign_1/BRSMACT_Campaign_1_Actigraphy/BRSMACT_Campagin_1_Actigraphy.csv"   # chính tả "Campagin" theo nguồn
MEASURES = {"efficiency": ("Sleep Efficiency (%)", "%"), "duration": ("Sleep Duration (hours)", "h"),
            "latency": ("Sleep Latency (hours)", "h")}


def _hours(v) -> float:
    """'7:44:00' | '0:14' | '0' → giờ thập phân; NA → NaN."""
    if pd.isna(v) or str(v).strip() in ("", "NA"):
        return np.nan
    parts = [float(x) for x in str(v).split(":")]
    return parts[0] + (parts[1] / 60 if len(parts) > 1 else 0) + (parts[2] / 3600 if len(parts) > 2 else 0)


def nights(raw: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hóa: subject_id, date, phase, efficiency, duration, latency, sedative."""
    out = pd.DataFrame({
        "subject_id": "utmb_c1:" + raw.Subject.astype(str),
        "date": pd.to_datetime(raw.Date, format="%m/%d/%Y"),
        "phase": raw.Test_Phase,
        "efficiency": pd.to_numeric(raw["Sleep Efficiency (%)"], errors="coerce"),
        "duration": raw["Sleep Duration (hours)"].map(_hours),
        "latency": raw["Sleep Latency (hours)"].map(_hours),
        "sedative": raw.Notes.fillna("").str.contains("ambien", case=False),
    })
    if out.duplicated(["subject_id", "date"]).any():
        raise ValueError("Trùng người/đêm trong actigraphy")
    return out.sort_values(["subject_id", "date"]).reset_index(drop=True)


def _grids(n: pd.DataFrame, measure: str):
    for sid, g in n.groupby("subject_id"):
        days = pd.date_range(g.date.min(), g.date.max(), freq="D")
        yield sid, g.set_index("date")[measure].reindex(days).to_numpy(float), days


def sleep_act_windows(n: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    w, names, parts = cfg["window"], check_features(cfg["features"]), []
    for sid, grid, days in _grids(n, cfg["measure"]):
        t = make_windows(grid, days, w["past"], w["future"], w["step"], names)
        if len(t):
            t.insert(0, "subject_id", sid)
            parts.append(t)
    return pd.concat(parts, ignore_index=True).rename(columns={"target": cfg["target"]})


def sleep_act_latest(n: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    names = check_features(cfg["features"])
    return pd.DataFrame([{"subject_id": sid, **latest_window(grid, days, cfg["window"]["past"], names)}
                         for sid, grid, days in _grids(n, cfg["measure"])])


def read_actigraphy(nlsp: Path) -> pd.DataFrame:
    manifest = pd.read_csv(nlsp / "download_manifest.csv", keep_default_na=False)
    with zipfile.ZipFile(nlsp / "BRSMAct.zip") as zf:
        return _verified_csv(zf, manifest, "BRSMAct.zip", MEMBER)


def build_sleep_act(data_dir: Path, cfg: dict) -> tuple[pd.DataFrame, list[str]]:
    if cfg["measure"] not in MEASURES:
        raise ValueError(f"measure phải là một trong {list(MEASURES)}")
    return sleep_act_windows(nights(read_actigraphy(data_dir / "raw/nlsp")), cfg), check_features(cfg["features"])


def from_csv(frame: pd.DataFrame, cfg: dict, kind: str) -> pd.DataFrame:
    """Cho bước predict: file CSV cùng định dạng nguồn (Subject, Date, Sleep … , Notes)."""
    n = nights(frame)
    return sleep_act_latest(n, cfg) if kind == "latest" else sleep_act_windows(n, cfg)


