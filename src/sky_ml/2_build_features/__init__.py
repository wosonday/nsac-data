"""Bước 2 – build_features: dữ liệu (data/1_source) → bảng đặc trưng theo cấu hình trong configs/tasks.yaml.

BUILD      : dùng ở bước 2 (tạo bảng train có target). Khóa = `builder` trong tasks.yaml (mặc định = tên task).
FOR_PREDICT: dùng ở bước 5 (biến file thô MỚI thành đặc trưng, cùng quy tắc với bước 2).
             Mọi task còn dùng được `--mode table` (đầu vào đã là bảng đặc trưng).
"""
from .cft70_nnx import build_glucose, build_mood, mood_latest, mood_windows
from .cpet import build_cpet
from .dose import COLUMNS as DOSE_COLUMNS
from .dose import build_dose, dose_latest, dose_windows
from .hr import COLUMNS as HR_COLUMNS
from .hr import build_hr, hr_latest, hr_windows
from .prepost import build_prepost
from .sleep import build_sleep
from .sleep_act import build_sleep_act, from_csv
from .vitals import build_vitals
from .windows import FEATURES

BUILD = {"hr": build_hr, "dose": build_dose, "cpet": build_cpet, "sleep": build_sleep, "sleep_act": build_sleep_act, "vitals": build_vitals,
         "mood": build_mood, "glucose": build_glucose,
         "prepost": build_prepost}
FOR_PREDICT = {"hr": {"columns": HR_COLUMNS, "latest": hr_latest, "backtest": hr_windows},
               "dose": {"columns": DOSE_COLUMNS, "latest": dose_latest, "backtest": dose_windows},
               "sleep_act": {"columns": None,
                             "latest": lambda raw, cfg: from_csv(raw, cfg, "latest"),
                             "backtest": lambda raw, cfg: from_csv(raw, cfg, "backtest")},
               "cpet": {}, "sleep": {}, "vitals": {}, "glucose": {}, "prepost": {},
               "mood": {"columns": None, "latest": mood_latest, "backtest": mood_windows}}
__all__ = ["BUILD", "FEATURES", "FOR_PREDICT"]
