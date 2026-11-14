"""Đặc trưng cửa sổ: danh sách đặc trưng được CHỌN trong configs/tasks.yaml (khóa `features`).

Mỗi đặc trưng là một hàm của đoạn quá khứ `x` (mảng numpy, phần tử cuối là điểm đo mới nhất).
Thêm đặc trưng mới: thêm một dòng vào FEATURES rồi ghi tên nó vào `features:` trong YAML.
"""
import numpy as np
import pandas as pd

FEATURES = {
    "last_value":     lambda x: x[-1],                    # giá trị đo cuối
    "mean_last_5":    lambda x: x[-5:].mean(),            # trung bình 5 điểm cuối
    "mean_all":       lambda x: x.mean(),                 # trung bình cả cửa sổ quá khứ
    "std_all":        lambda x: x.std(),                  # độ dao động
    "change_last_10": lambda x: x[-1] - x[-10],           # thay đổi so với 10 điểm trước
    "min_all":        lambda x: x.min(),
    "max_all":        lambda x: x.max(),
    # đặc trưng bổ sung (chưa dùng trong cấu hình tái lập 11/11):
    "median_all":     lambda x: float(np.median(x)),
    "range_all":      lambda x: x.max() - x.min(),
    "slope_all":      lambda x: float(np.polyfit(np.arange(len(x)), x, 1)[0]),  # xu hướng / điểm
}


def check_features(names: list[str]) -> list[str]:
    unknown = [n for n in names if n not in FEATURES]
    if unknown:
        raise ValueError(f"Đặc trưng không tồn tại: {unknown}. Có sẵn: {sorted(FEATURES)}")
    return list(names)


def window_features(x: np.ndarray, names: list[str]) -> dict:
    """Đặc trưng tính CHỈ từ đoạn quá khứ `x` (dùng chung cho train và dự báo)."""
    return {n: FEATURES[n](x) for n in names}


def make_windows(values, times, past: int, future: int, step: int, names: list[str]) -> pd.DataFrame:
    """Cửa sổ CÓ target (để train / backtest). Cửa sổ chạm điểm thiếu bị bỏ, không nội suy."""
    rows = []
    for end in range(past, len(values) - future + 1, step):
        x, y = values[end - past:end], values[end:end + future]   # đặc trưng chỉ từ quá khứ
        if np.isnan(x).any() or np.isnan(y).any():
            continue
        rows.append({"cutoff_time": times[end - 1], **window_features(x, names), "target": y.mean()})
    return pd.DataFrame(rows)


def latest_window(values, times, past: int, names: list[str]) -> dict:
    """Đặc trưng của `past` điểm CUỐI (để dự báo tương lai chưa xảy ra). Thiếu dữ liệu → NaN."""
    empty = dict.fromkeys(names, np.nan)
    if len(values) < past:
        return {"cutoff_time": times[-1] if len(times) else None, **empty}
    x = values[-past:]
    return {"cutoff_time": times[-1], **(empty if np.isnan(x).any() else window_features(x, names))}
