"""RadLab Lidal (ISS, Columbus, 2022) → cửa sổ quá khứ `past` bước 5 phút → liều trung bình `future` bước tới.

Port NASA-cl prepare_dose: mốc thời gian lặp với giá trị khác nhau → bỏ cả mốc (không biết giá trị nào đúng);
lưới đều 5 phút, điểm thiếu = NaN (cửa sổ chạm NaN bị bỏ, không nội suy). Thời gian giữ như nguồn (chưa xác minh UTC).

`context` (tùy chọn, vd. [latitude, longitude, altitude]): giá trị TẠI cutoff — vị trí hiện tại của ISS,
biết được lúc dự báo. Không dùng vị trí tương lai (cần quỹ đạo dự báo, chưa có).
"""
from pathlib import Path

import numpy as np
import pandas as pd

from .windows import check_features, latest_window, make_windows

COLUMNS = ["timestamp", "absorbed_dose_rate"]
CONTEXT = ["latitude", "longitude", "altitude"]
SUBJECT = "radlab:Lidal"            # một chuỗi thiết bị, không phải người


def _grid(raw: pd.DataFrame, context: list[str], freq: str = "5min") -> pd.DataFrame:
    raw = raw.assign(timestamp=pd.to_datetime(raw.timestamp)).dropna(subset=["absorbed_dose_rate"])
    n_values = raw.groupby("timestamp").absorbed_dose_rate.transform("nunique")
    raw = raw[n_values == 1].drop_duplicates("timestamp")
    grid = pd.date_range(raw.timestamp.min().floor("D"), raw.timestamp.max().ceil("D"), freq=freq, inclusive="left")
    return raw.set_index("timestamp")[["absorbed_dose_rate", *context]].reindex(grid)


def _add_context(table: pd.DataFrame, frame: pd.DataFrame, context: list[str]) -> pd.DataFrame:
    if context:
        values = frame.loc[pd.to_datetime(table.cutoff_time), context].to_numpy()
        for i, c in enumerate(context):
            table[f"{c}_now"] = values[:, i]
    return table


def context_features(cfg: dict) -> list[str]:
    unknown = set(cfg.get("context", [])) - set(CONTEXT)
    if unknown:
        raise ValueError(f"context không hợp lệ: {sorted(unknown)}; có: {CONTEXT}")
    return [f"{c}_now" for c in cfg.get("context", [])]


def dose_windows(raw: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    cfg = normalize(cfg)
    w, names, ctx = cfg["window"], check_features(cfg["features_window"]), cfg.get("context", [])
    frame = _grid(raw, ctx)
    table = make_windows(frame.absorbed_dose_rate.to_numpy(float), frame.index, w["past"], w["future"], w["step"], names)
    table = _add_context(table, frame, ctx).dropna().reset_index(drop=True)
    table.insert(0, "subject_id", SUBJECT)
    return table.rename(columns={"target": cfg["target"]})


def dose_latest(raw: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    cfg = normalize(cfg)
    ctx = cfg.get("context", [])
    frame = _grid(raw, ctx)
    series = frame.absorbed_dose_rate.to_numpy(float)
    last = np.flatnonzero(~np.isnan(series))[-1] + 1          # bỏ phần lưới trống sau điểm đo cuối
    row = latest_window(series[:last], frame.index[:last], cfg["window"]["past"], check_features(cfg["features_window"]))
    return _add_context(pd.DataFrame([{"subject_id": SUBJECT, **row}]), frame, ctx)


def read_dose(paths: list[Path], context: list[str] = ()) -> pd.DataFrame:
    return pd.concat([pd.read_csv(p, usecols=COLUMNS + list(context)) for p in sorted(paths)], ignore_index=True)


def normalize(cfg: dict) -> dict:
    """`features` trong YAML = đặc trưng cửa sổ; cột context được thêm tự động (tên <cột>_now)."""
    return {**cfg, "features_window": cfg.get("features_window", cfg["features"])}


def build_dose(data_dir: Path, cfg: dict) -> tuple[pd.DataFrame, list[str]]:
    cfg = normalize(cfg)
    extra = context_features(cfg)                       # kiểm context trước khi đọc file
    raw = read_dose([data_dir / p for p in cfg["inputs"]], cfg.get("context", []))
    return dose_windows(raw, cfg), check_features(cfg["features_window"]) + extra
