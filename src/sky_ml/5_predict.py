"""Bước 5 – predict: nạp mô hình ĐÃ HUẤN LUYỆN (3_models) và dự báo cho dữ liệu MỚI.

Hai chế độ:
- latest   : dự báo tương lai chưa xảy ra từ đoạn dữ liệu cuối của mỗi người (dùng cho ứng dụng).
- backtest : dự báo các cửa sổ đã biết đáp án để so sai số (kiểm tra mô hình trên người mới).
Khoảng 90% lấy từ sai số OOF của chính mô hình đó (bước 3) — không lấy từ dữ liệu đang dự báo.
"""
import importlib
import math

import numpy as np
import pandas as pd

evaluate = importlib.import_module("sky_ml.4_evaluate")  # bước số không import trực tiếp được


def calibration_half_width(oof: pd.DataFrame, model: str, alpha: float) -> float:
    """Nửa độ rộng khoảng (1-alpha) từ |sai số| OOF của `model` (split-conformal)."""
    errors = (oof.y_true - oof.y_pred).abs()[oof.model == model]
    return evaluate.interval_half_width(errors, alpha)


def predict_rows(model, rows: pd.DataFrame, features: list[str], half_width: float,
                 train_table: pd.DataFrame, cfg: dict, model_name: str) -> pd.DataFrame:
    """Mỗi hàng → dự báo + khoảng 90% hoặc từ chối (abstain) kèm lý do."""
    lo, hi = train_table[features].min(), train_table[features].max()
    train_subjects = set(train_table.subject_id)
    out = rows[["subject_id", "cutoff_time"]].copy()
    out["model"], out["unit"] = model_name, cfg.get("unit")
    reasons = []
    for _, row in rows.iterrows():
        r = []
        x = row[features].astype(float)
        if x.isna().any():
            r.append("missing_features")
        elif ((x < lo) | (x > hi)).any():
            r.append("out_of_training_range")       # ngoài miền đã học → không ngoại suy
        if not math.isfinite(half_width):
            r.append("insufficient_calibration_data")
        reasons.append(r)
    ok = np.array([not r for r in reasons])
    pred = np.full(len(rows), np.nan)
    if ok.any():
        pred[ok] = model.predict(rows.loc[ok, features].astype(float))
    out["prediction"] = pred
    out["low90"], out["high90"] = pred - half_width, pred + half_width
    out["abstain"] = ~ok
    out["reasons"] = [";".join(r) for r in reasons]
    # Người đã có trong dữ liệu huấn luyện: mô hình final đã "thấy" họ → không phải đánh giá trên người mới.
    out["in_sample"] = out.subject_id.isin(train_subjects)
    if cfg["target"] in rows:                        # chế độ backtest: có đáp án
        out["y_true"] = rows[cfg["target"]].to_numpy()
        out["abs_error"] = (out.y_true - out.prediction).abs()
    return out
