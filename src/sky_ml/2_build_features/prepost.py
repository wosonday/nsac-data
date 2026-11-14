"""Đo theo ĐỢT (trước / trong / sau nằm giường) → một hàng / người: % thay đổi từ PRE đến một mốc đích.

Dùng chung cho iDXA (khối nạc chân, khối khoáng xương), siêu âm tim (đường kính thất trái)… — mọi tham số ở tasks.yaml:
  archive, member (đường dẫn trong ZIP), value_column, phase_column, day_column, target_phase, target_day, change.
Baseline = trung bình MỌI lần đo PRE của người đó (giảm nhiễu đo) — hoặc (baseline_phase, baseline_day) nếu khai báo
(vd. lipid chỉ đo trong nằm giường: baseline = ngày 14). Target = giá trị tại (target_phase, target_day).
Kiểm SHA-256 + MD5 member theo raw/nlsp/download_manifest.csv. Không dùng nhóm can thiệp làm đặc trưng.
"""
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from .cpet import _verified_csv

FEATURES = ["baseline"]


def read_member(nlsp: Path, archive: str, member: str) -> pd.DataFrame:
    manifest = pd.read_csv(nlsp / "download_manifest.csv", keep_default_na=False)
    with zipfile.ZipFile(nlsp / archive) as zf:
        return _verified_csv(zf, manifest, archive, member)


def prepost_table(raw: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    phase = raw[cfg["phase_column"]].astype(str).str.upper().str.replace("-", "_").str.strip()
    day = pd.to_numeric(raw[cfg["day_column"]].astype(str).str.extract(r"^\s*(-?\d+)")[0], errors="coerce")
    value = pd.to_numeric(raw[cfg["value_column"]], errors="coerce")
    f = pd.DataFrame({"subject_id": "utmb_cft70:" + raw.Subject.astype(str).str.strip(), "phase": phase,
                      "day": day, "value": value}).dropna(subset=["value"])
    rows = []
    for sid, g in f.groupby("subject_id"):
        bphase, bday = cfg.get("baseline_phase", "PRE_TEST"), cfg.get("baseline_day")
        bmask = g.phase.eq(bphase) & (g.day.eq(bday) if bday is not None else True)
        base = g[bmask].value.mean()
        tgt = g[g.phase.eq(cfg["target_phase"]) & g.day.eq(cfg["target_day"])].value.mean()
        if not (np.isfinite(base) and np.isfinite(tgt)) or base == 0:
            continue
        change = 100 * (tgt / base - 1) if cfg.get("change", "percent") == "percent" else tgt - base
        rows.append({"subject_id": sid, "baseline": base, "n_pre": int(bmask.sum()), cfg["target"]: change})
    return pd.DataFrame(rows)


def build_prepost(data_dir: Path, cfg: dict) -> tuple[pd.DataFrame, list[str]]:
    raw = read_member(data_dir / "raw/nlsp", cfg["archive"], cfg["member"])
    table = prepost_table(raw, cfg)
    unknown = set(cfg["features"]) - set(FEATURES)
    if unknown:
        raise ValueError(f"Đặc trưng prepost không tồn tại: {sorted(unknown)}; có: {FEATURES}")
    return table.drop(columns=["n_pre"]), list(cfg["features"])
