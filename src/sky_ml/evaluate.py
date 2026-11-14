"""Bước evaluate: so baseline (theo đơn vị độc lập = người/tháng), CI95 bootstrap, độ bao phủ khoảng 90%."""
import math

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, cohen_kappa_score, f1_score


def bootstrap_ci(values, n_samples: int, seed: int = 0) -> tuple[float, float]:
    """CI95 của giá trị trung bình, lấy mẫu lại CÁC ĐƠN VỊ (không lấy lại từng dòng)."""
    values = np.asarray(values, dtype=float)
    means = np.random.default_rng(seed).choice(values, (n_samples, len(values))).mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def score(group: pd.DataFrame, kind: str) -> float:
    if kind == "regression":
        return float(np.mean(np.abs(group.y_true - group.y_pred)))   # MAE: càng nhỏ càng tốt
    return float(f1_score(group.y_true, group.y_pred, average="macro"))  # macro-F1: càng lớn càng tốt


def score_per_fold(oof: pd.DataFrame, kind: str) -> pd.DataFrame:
    return oof.groupby(["fold", "model"]).apply(score, kind=kind, include_groups=False).unstack("model")


def evaluate(oof: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    kind, n_boot = cfg["kind"], cfg.get("bootstrap_samples", 10000)
    metric = "mae" if kind == "regression" else "macro_f1"
    per_fold = score_per_fold(oof, kind)
    baseline = per_fold[cfg["baseline"]]
    rows = []
    for model in per_fold.columns:
        diff = per_fold[model] - baseline                    # so cặp trên cùng một người/tháng
        low, high = bootstrap_ci(per_fold[model], n_boot)
        dlow, dhigh = bootstrap_ci(diff, n_boot)
        row = {"model": model, "units": len(per_fold), metric: per_fold[model].mean(), "ci95_low": low,
               "ci95_high": high, "diff_vs_baseline": diff.mean(), "diff_ci95_low": dlow, "diff_ci95_high": dhigh}
        pooled = oof[oof.model == model]
        if kind == "regression":
            row["rmse"] = float(np.sqrt(np.mean((pooled.y_true - pooled.y_pred) ** 2)))
        else:
            truth = np.column_stack([pooled.y_true == c for c in cfg["classes"]]).astype(float)
            proba = pooled[[f"p_{c}" for c in cfg["classes"]]].to_numpy()
            row["balanced_accuracy"] = balanced_accuracy_score(pooled.y_true, pooled.y_pred)
            row["cohen_kappa"] = cohen_kappa_score(pooled.y_true, pooled.y_pred)
            row["brier"] = float(np.mean(np.sum((proba - truth) ** 2, axis=1)))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(metric, ascending=kind == "regression").reset_index(drop=True)


def interval_half_width(abs_errors, alpha: float) -> float:
    """Split-conformal: phân vị bậc ceil((n+1)(1-alpha)) của |sai số|; quá ít sai số → vô hạn."""
    errors = np.sort(np.asarray(abs_errors, dtype=float))
    k = math.ceil((len(errors) + 1) * (1 - alpha))
    return math.inf if k > len(errors) else float(errors[k - 1])


def interval_coverage(oof: pd.DataFrame, model: str, alpha: float) -> dict:
    """Độ rộng cho fold k tính CHỈ từ sai số của các fold khác → đếm tỷ lệ fold k nằm trong khoảng."""
    r = oof[oof.model == model].assign(abs_error=lambda d: (d.y_true - d.y_pred).abs())
    inside, widths = [], []
    for fold, part in r.groupby("fold"):
        hw = interval_half_width(r.abs_error[r.fold != fold], alpha)
        inside.extend(part.abs_error <= hw)
        widths.append(hw)
    return {"model": model, "target_coverage": 1 - alpha,
            "observed_coverage": float(np.mean(inside)), "median_half_width": float(np.median(widths))}


def confusion(oof: pd.DataFrame, model: str, classes: list[str]) -> pd.DataFrame:
    r = oof[oof.model == model]
    return pd.crosstab(r.y_true, r.y_pred).reindex(index=classes, columns=classes, fill_value=0)
