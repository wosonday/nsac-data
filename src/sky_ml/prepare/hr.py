"""MMASH (sample-v2) → một hàng / cửa sổ 30 phút của một người."""

from pathlib import Path

import numpy as np
import pandas as pd

from .windows import WINDOW_FEATURES, make_windows


def prepare_hr(data_dir: Path, cfg: dict) -> tuple[pd.DataFrame, list[str]]:
    minutes = pd.read_csv(
        data_dir / cfg["inputs"][0],
        usecols=["subject_id", "minute_start_s", "hr_from_ibi_bpm_mean"],
    )
    low, high, w = *cfg["valid_hr_range"], cfg["window"]
    parts = []
    for subject_id, person in minutes.groupby("subject_id"):
        minute = (person.minute_start_s // 60).astype(int).to_numpy()
        hr = person.hr_from_ibi_bpm_mean.to_numpy(dtype=float, copy=True)
        hr[(hr < low) | (hr > high)] = np.nan  # số đo không khả dĩ → thiếu
        grid = np.full(
            minute.max() - minute.min() + 1, np.nan
        )  # lưới 1 phút, phút vắng = NaN
        grid[minute - minute.min()] = hr
        windows = make_windows(
            grid, np.arange(len(grid)), w["past"], w["future"], w["step"]
        )
        if len(windows):
            windows.insert(0, "subject_id", subject_id)
            parts.append(windows)
    table = pd.concat(parts, ignore_index=True).rename(
        columns={"target": cfg["target"]}
    )
    return table, WINDOW_FEATURES
