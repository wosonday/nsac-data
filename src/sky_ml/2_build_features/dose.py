"""RadLab Lidal (ISS, Columbus, 2022) → cửa sổ quá khứ `past` bước 5 phút → liều trung bình `future` bước tới.

Port NASA-cl prepare_dose: mốc thời gian lặp với giá trị khác nhau → bỏ cả mốc (không biết giá trị nào đúng);
lưới đều 5 phút, điểm thiếu = NaN (cửa sổ chạm NaN bị bỏ, không nội suy). Thời gian giữ như nguồn (chưa xác minh UTC).
"""
from pathlib import Path

import numpy as np
import pandas as pd

from .windows import check_features, latest_window, make_windows

COLUMNS = ["timestamp", "absorbed_dose_rate"]
SUBJECT = "radlab:Lidal"            # một chuỗi thiết bị, không phải người


def _grid(raw: pd.DataFrame, freq: str = "5min") -> tuple[np.ndarray, pd.DatetimeIndex]:
    raw = raw.assign(timestamp=pd.to_datetime(raw.timestamp)).dropna(subset=["absorbed_dose_rate"])
    n_values = raw.groupby("timestamp").absorbed_dose_rate.transform("nunique")
    raw = raw[n_values == 1].drop_duplicates("timestamp")
    grid = pd.date_range(raw.timestamp.min().floor("D"), raw.timestamp.max().ceil("D"), freq=freq, inclusive="left")
    return raw.set_index("timestamp").absorbed_dose_rate.reindex(grid).to_numpy(dtype=float), grid


def dose_windows(raw: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    w, names = cfg["window"], check_features(cfg["features"])
    series, grid = _grid(raw)
    table = make_windows(series, grid, w["past"], w["future"], w["step"], names)
    table.insert(0, "subject_id", SUBJECT)
    return table.rename(columns={"target": cfg["target"]})


def dose_latest(raw: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    series, grid = _grid(raw)
    last = np.flatnonzero(~np.isnan(series))[-1] + 1          # bỏ phần lưới trống sau điểm đo cuối
    row = latest_window(series[:last], grid[:last], cfg["window"]["past"], check_features(cfg["features"]))
    return pd.DataFrame([{"subject_id": SUBJECT, **row}])


def read_dose(paths: list[Path]) -> pd.DataFrame:
    return pd.concat([pd.read_csv(p, usecols=COLUMNS) for p in sorted(paths)], ignore_index=True)


def build_dose(data_dir: Path, cfg: dict) -> tuple[pd.DataFrame, list[str]]:
    return dose_windows(read_dose([data_dir / p for p in cfg["inputs"]]), cfg), check_features(cfg["features"])
