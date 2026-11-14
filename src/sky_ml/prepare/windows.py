"""Cắt chuỗi đều thành cửa sổ: `past` điểm quá khứ → trung bình `future` điểm kế tiếp."""

import numpy as np
import pandas as pd

WINDOW_FEATURES = [
    "last_value",
    "mean_last_5",
    "mean_all",
    "std_all",
    "change_last_10",
    "min_all",
    "max_all",
]


def make_windows(values, times, past: int, future: int, step: int) -> pd.DataFrame:
    rows = []
    for end in range(past, len(values) - future + 1, step):
        x, y = (
            values[end - past : end],
            values[end : end + future],
        )  # đặc trưng chỉ từ quá khứ
        if np.isnan(x).any() or np.isnan(y).any():  # không nội suy qua chỗ thiếu
            continue
        rows.append(
            {
                "cutoff_time": times[end - 1],
                "last_value": x[-1],
                "mean_last_5": x[-5:].mean(),
                "mean_all": x.mean(),
                "std_all": x.std(),
                "change_last_10": x[-1] - x[-10],
                "min_all": x.min(),
                "max_all": x.max(),
                "target": y.mean(),
            }
        )
    return pd.DataFrame(rows)
