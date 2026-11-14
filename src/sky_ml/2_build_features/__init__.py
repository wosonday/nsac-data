"""Bước 2 – build_features: dữ liệu (data/) → bảng đặc trưng theo cấu hình trong configs/tasks.yaml.

BUILD      : dùng ở bước 2 (tạo bảng train có target).
FOR_PREDICT: dùng ở bước 5 (biến file đầu vào MỚI thành đặc trưng, cùng quy tắc với bước 2).
"""
from .hr import COLUMNS as HR_COLUMNS
from .hr import build_hr, hr_latest, hr_windows
from .windows import FEATURES

BUILD = {"hr": build_hr}
FOR_PREDICT = {"hr": {"columns": HR_COLUMNS, "latest": hr_latest, "backtest": hr_windows}}
__all__ = ["BUILD", "FEATURES", "FOR_PREDICT"]
