"""Bước 5 – predict: nạp mô hình ĐÃ HUẤN LUYỆN (3_models) và dự báo cho dữ liệu MỚI.

Ba chế độ:
- latest   : dự báo tương lai chưa xảy ra từ đoạn dữ liệu cuối của mỗi người/chuỗi (hr, dose).
- backtest : dự báo các cửa sổ đã biết đáp án để so sai số (hr, dose).
- table    : file đầu vào ĐÃ là bảng đặc trưng (subject_id + các cột trong features.json; mọi task).
Hồi quy: khoảng 90% lấy từ sai số OOF của chính mô hình đó (bước 3). Phân loại: nhãn + xác suất từng lớp.
"""
import importlib
import math

import numpy as np
import pandas as pd

evaluate = importlib.import_module("sky_ml.4_evaluate")  # bước số không import trực tiếp được


def calibration_half_width(oof: pd.DataFrame, model: str, alpha: float, kind: str = "regression") -> float:
    """Nửa độ rộng khoảng (1-alpha) từ |sai số| OOF của `model` (split-conformal). Phân loại → NaN."""
    if kind != "regression":
        return math.nan
    errors = (oof.y_true - oof.y_pred).abs()[oof.model == model]
    return evaluate.interval_half_width(errors, alpha)


def predict_rows(model, rows: pd.DataFrame, features: list[str], half_width: float,
                 train_table: pd.DataFrame, cfg: dict, model_name: str) -> pd.DataFrame:
    """Mỗi hàng → dự báo + khoảng 90% hoặc từ chối (abstain) kèm lý do."""
    lo, hi = train_table[features].min(), train_table[features].max()
    train_subjects = set(train_table.subject_id)
    classify = cfg.get("kind") == "classification"
    out = rows[[c for c in ("subject_id", "cutoff_time", "epoch") if c in rows]].copy()
    out["model"], out["unit"] = model_name, cfg.get("unit")
    reasons = []
    for _, row in rows.iterrows():
        r = []
        x = row[features].astype(float)
        if x.isna().any():
            r.append("missing_features")
        elif ((x < lo) | (x > hi)).any():
            r.append("out_of_training_range")       # ngoài miền đã học → không ngoại suy
        if not classify and not math.isfinite(half_width):
            r.append("insufficient_calibration_data")
        reasons.append(r)
    ok = np.array([not r for r in reasons])
    pred = np.full(len(rows), np.nan, dtype=object if classify else float)
    if ok.any():
        pred[ok] = model.predict(rows.loc[ok, features].astype(float))
    out["prediction"] = pred
    if classify:                                     # xác suất từng lớp (không có khoảng 90%)
        proba = np.full((len(rows), len(cfg["classes"])), np.nan)
        if ok.any():
            p = pd.DataFrame(model.predict_proba(rows.loc[ok, features].astype(float)), columns=model.classes_)
            proba[ok] = p.reindex(columns=cfg["classes"], fill_value=0.0).to_numpy()
        for i, c in enumerate(cfg["classes"]):
            out[f"p_{c}"] = proba[:, i]
    else:
        out["low90"], out["high90"] = pred - half_width, pred + half_width
    out["abstain"] = ~ok
    out["reasons"] = [";".join(r) for r in reasons]
    # Người đã có trong dữ liệu huấn luyện: mô hình final đã "thấy" họ → không phải đánh giá trên người mới.
    out["in_sample"] = out.subject_id.isin(train_subjects)
    if cfg["target"] in rows:                        # chế độ backtest: có đáp án
        out["y_true"] = rows[cfg["target"]].to_numpy()
        if classify:
            out["correct"] = out.y_true == out.prediction
        else:
            out["abs_error"] = (out.y_true - out.prediction).abs()
    return out


def table_rows(frame: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Chế độ `table`: đầu vào đã là đặc trưng; chỉ kiểm có subject_id."""
    if "subject_id" not in frame:
        raise ValueError("Chế độ table cần cột subject_id + các cột đặc trưng trong features.json")
    return frame
