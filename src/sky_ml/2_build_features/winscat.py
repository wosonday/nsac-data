"""UTMB MR085G WinSCAT (bộ test nhận thức trên máy tính của NASA) → điểm của LẦN TEST TỚI từ `past` lần trước.

TRAIN: Campaign 3 (26 file, 1 người/file). NGOÀI cohort: Campaign 1 (C1G0001–3 = tomas, yuki, noor).
Chuỗi theo THỨ TỰ NGÀY TEST (Date + Time); mỗi lần test là một điểm. `measure` = tên cột nguồn, vd. CPTRT
(thời gian phản ứng test hiệu suất liên tục, ms — thấp hơn là tốt hơn), MTHA (độ chính xác toán, %)…
"""
import zipfile
from pathlib import Path

import pandas as pd

from .cpet import _verified_csv
from .windows import check_features, make_windows

COHORTS = {"campaign_3": ("campaign_3/", "utmb_c3:"), "campaign_1": ("campaign_1/MR085G_Campaign_1_WinSCAT/MR085G_Campaign_1_WinSCAT_All.csv", "utmb_c1:")}


def read_winscat(nlsp: Path, cohorts: list[str], measure: str) -> pd.DataFrame:
    manifest = pd.read_csv(nlsp / "download_manifest.csv", keep_default_na=False)
    parts = []
    with zipfile.ZipFile(nlsp / "MR085G.zip") as zf:
        for cohort in cohorts:
            prefix, ns = COHORTS[cohort]
            for m in sorted(x for x in zf.namelist() if x.startswith(prefix) and x.endswith(".csv") and "WinSCAT" in x):
                d = _verified_csv(zf, manifest, "MR085G.zip", m)
                when = pd.to_datetime(d.Date.astype(str) + " " + d.Time.astype(str), format="%m/%d/%Y %H:%M:%S", errors="coerce")
                parts.append(pd.DataFrame({"subject_id": ns + d.Subject.astype(str), "cohort": cohort, "when": when,
                                           "value": pd.to_numeric(d[measure], errors="coerce")}))
    f = pd.concat(parts, ignore_index=True).dropna(subset=["when"])
    return f.drop_duplicates(["subject_id", "when"]).sort_values(["subject_id", "when"]).reset_index(drop=True)


def winscat_windows(f: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    w, names, parts = cfg["window"], check_features(cfg["features"]), []
    for sid, g in f.groupby("subject_id"):
        t = make_windows(g.value.to_numpy(float), g.when.to_numpy(), w["past"], w["future"], w["step"], names)
        if len(t):
            t.insert(0, "subject_id", sid)
            parts.append(t)
    return pd.concat(parts, ignore_index=True).rename(columns={"target": cfg["target"]})


def build_winscat(data_dir: Path, cfg: dict) -> tuple[pd.DataFrame, list[str]]:
    nlsp = data_dir / "raw/nlsp"
    table = winscat_windows(read_winscat(nlsp, [cfg["train_cohort"]], cfg["measure"]), cfg)
    if cfg.get("external_cohorts"):
        table.attrs["external"] = winscat_windows(read_winscat(nlsp, cfg["external_cohorts"], cfg["measure"]), cfg)
    return table, check_features(cfg["features"])
