"""UTMB CFT70 – NNX10AP86G (24 người, nằm giường 70 ngày): POMS (tâm trạng) và OGTT (đường huyết).

mood    : điểm Total Mood Disturbance (TMD) của LẦN ĐO TỚI (~1 tuần) từ `past` lần đo trước.
glucose : thay đổi đường huyết lúc đói (OGTT phút 0) từ PRE → cuối nằm giường (BR66); một hàng / người.
Kiểm SHA-256 + MD5 member ZIP theo download_manifest.csv. Không dùng nhóm can thiệp (Treatment/Group) làm đặc trưng
vì phi hành gia thật không có. Ngày nghiên cứu: PRE = −BR_Day, IN = +BR_Day, POST = 70 + BR_Day.
"""
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from .cpet import _verified_csv
from .windows import check_features, latest_window, make_windows

ROOT = "cft70/NNX10AP86G_CFT70/NNX10AP86G_CFT70_"
BED_REST_DAYS = 70


def _read(nlsp: Path, name: str) -> pd.DataFrame:
    manifest = pd.read_csv(nlsp / "download_manifest.csv", keep_default_na=False)
    with zipfile.ZipFile(nlsp / "NNX10AP86G.zip") as zf:
        return _verified_csv(zf, manifest, "NNX10AP86G.zip", ROOT + name)


def _study_day(phase: pd.Series, br_day: pd.Series) -> pd.Series:
    p = phase.str.upper().str.replace("-", "_")
    d = pd.to_numeric(br_day, errors="coerce")
    return np.select([p.eq("PRE_TEST"), p.eq("IN_TEST"), p.eq("POST_TEST")], [-d, d, BED_REST_DAYS + d], np.nan)


# ------------------------------------------------------------------------------------------- mood (POMS)
def poms(nlsp: Path) -> pd.DataFrame:
    raw = _read(nlsp, "POMS_TMD.csv")
    out = pd.DataFrame({"subject_id": "utmb_cft70:" + raw.Subject.astype(str),
                        "study_day": _study_day(raw.Test_Phase, raw.BR_Day),
                        "tmd": pd.to_numeric(raw["Total Mood Disturbance (TMD)"], errors="coerce")})
    return out.dropna(subset=["study_day"]).sort_values(["subject_id", "study_day"]).reset_index(drop=True)


def mood_windows(assess: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Chuỗi theo THỨ TỰ lần đo (không phải lưới ngày); lần đo NA → cửa sổ chạm nó bị bỏ."""
    w, names, parts = cfg["window"], check_features(cfg["features"]), []
    for sid, g in assess.groupby("subject_id"):
        t = make_windows(g.tmd.to_numpy(float), g.study_day.to_numpy(), w["past"], w["future"], w["step"], names)
        if len(t):
            t.insert(0, "subject_id", sid)
            parts.append(t)
    return pd.concat(parts, ignore_index=True).rename(columns={"target": cfg["target"]})


def mood_latest(assess: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Bước predict: đầu vào dạng dài (subject_id, study_day, tmd) — thật hoặc giả định."""
    names = check_features(cfg["features"])
    return pd.DataFrame([{"subject_id": sid, **latest_window(g.tmd.to_numpy(float), g.study_day.to_numpy(),
                                                             cfg["window"]["past"], names)}
                         for sid, g in assess.sort_values(["subject_id", "study_day"]).groupby("subject_id")])


def build_mood(data_dir: Path, cfg: dict) -> tuple[pd.DataFrame, list[str]]:
    return mood_windows(poms(data_dir / "raw/nlsp"), cfg), check_features(cfg["features"])


# ------------------------------------------------------------------------------------------- glucose (OGTT)
GLUCOSE_FEATURES = ["pre_glucose_0", "pre_glucose_120", "pre_insulin_0"]


def ogtt(nlsp: Path) -> pd.DataFrame:
    raw = _read(nlsp, "OGTT.csv")
    return pd.DataFrame({"subject_id": "utmb_cft70:" + raw.Subject.astype(str),
                         "phase": raw["Test Phase"].str.upper(), "study_day": _study_day(raw["Test Phase"], raw["BR Day"]),
                         "minute": pd.to_numeric(raw["OGTT Time"], errors="coerce"),
                         "glucose": pd.to_numeric(raw["Glucose (mg/dL)"], errors="coerce"),
                         "insulin": pd.to_numeric(raw["Insulin (uU/mL)"], errors="coerce")})


def glucose_table(o: pd.DataFrame, target_day: int) -> pd.DataFrame:
    """Một hàng / người: trung bình các lần PRE → glucose lúc đói tại `target_day` (IN) trừ PRE."""
    rows = []
    for sid, g in o.groupby("subject_id"):
        pre = g[g.phase.eq("PRE_TEST")]
        g0 = pre[pre.minute.eq(0)].glucose.mean()
        tgt = g[g.study_day.eq(target_day) & g.minute.eq(0)].glucose
        rows.append({"subject_id": sid, "pre_glucose_0": g0,
                     "pre_glucose_120": pre[pre.minute.eq(120)].glucose.mean(),
                     "pre_insulin_0": pre[pre.minute.eq(0)].insulin.mean(),
                     "delta_glucose_0": (tgt.mean() - g0) if len(tgt.dropna()) else np.nan})
    return pd.DataFrame(rows).dropna().reset_index(drop=True)


def build_glucose(data_dir: Path, cfg: dict) -> tuple[pd.DataFrame, list[str]]:
    table = glucose_table(ogtt(data_dir / "raw/nlsp"), cfg["target_study_day"])
    unknown = set(cfg["features"]) - set(GLUCOSE_FEATURES)
    if unknown:
        raise ValueError(f"Đặc trưng glucose không tồn tại: {sorted(unknown)}; có: {GLUCOSE_FEATURES}")
    return table, list(cfg["features"])
