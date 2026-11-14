"""MMASH (sample-v2) → bảng đặc trưng HR: cửa sổ quá khứ → HR trung bình `future` phút tới.

Tham số đọc từ configs/tasks.yaml: window, valid_hr_range, features, target.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from .windows import check_features, latest_window, make_windows

COLUMNS = ["subject_id", "minute_start_s", "hr_from_ibi_bpm_mean"]


def _grids(minutes: pd.DataFrame, cfg: dict):
    """Mỗi người → (subject_id, lưới HR 1 phút, chỉ số phút). Phút vắng / HR ngoài miền kỹ thuật = NaN."""
    low, high = cfg["valid_hr_range"]
    for subject_id, person in minutes.groupby("subject_id"):
        minute = (person.minute_start_s // 60).astype(int).to_numpy()
        hr = person.hr_from_ibi_bpm_mean.to_numpy(dtype=float, copy=True)
        hr[(hr < low) | (hr > high)] = np.nan
        grid = np.full(minute.max() - minute.min() + 1, np.nan)
        grid[minute - minute.min()] = hr
        yield subject_id, grid, np.arange(minute.min(), minute.max() + 1)


def hr_windows(minutes: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Cửa sổ có target (train / backtest). `cutoff_time` = chỉ số trong lưới của người đó."""
    w, names, parts = cfg["window"], check_features(cfg["features"]), []
    for subject_id, grid, _ in _grids(minutes, cfg):
        windows = make_windows(grid, np.arange(len(grid)), w["past"], w["future"], w["step"], names)
        if len(windows):
            windows.insert(0, "subject_id", subject_id)
            parts.append(windows)
    return pd.concat(parts, ignore_index=True).rename(columns={"target": cfg["target"]})


def hr_latest(minutes: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Một hàng / người: đặc trưng đoạn cuối → dự báo `future` phút TỚI. `cutoff_time` = phút thật."""
    names = check_features(cfg["features"])
    return pd.DataFrame([{"subject_id": s, **latest_window(grid, times, cfg["window"]["past"], names)}
                         for s, grid, times in _grids(minutes, cfg)])


def build_hr(data_dir: Path, cfg: dict) -> tuple[pd.DataFrame, list[str]]:
    minutes = pd.read_csv(data_dir / cfg["inputs"][0], usecols=COLUMNS)
    return hr_windows(minutes, cfg), check_features(cfg["features"])
