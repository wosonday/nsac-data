"""Bước train: chia fold (theo người / theo tháng), fit MỌI mô hình trên CÙNG các fold, trả dự đoán OOF."""
import pandas as pd
from sklearn.base import clone

from .models import build_model


def make_folds(table: pd.DataFrame, split: dict) -> list[dict]:
    """[{name, train, test}] — train/test là chỉ số hàng của `table`. Fold rỗng bị bỏ qua."""
    folds = []
    if split["type"] == "leave_one_subject_out":
        for subject in table.subject_id.unique():
            is_test = table.subject_id == subject
            folds.append({"name": subject, "train": table.index[~is_test], "test": table.index[is_test]})
    elif split["type"] == "by_month":
        time = pd.to_datetime(table.cutoff_time)
        for month in split["test_months"]:
            is_test = time.dt.month == month
            if not is_test.any():
                continue
            start = pd.Timestamp(year=time[is_test].min().year, month=month, day=1)
            is_train = time < start - pd.Timedelta(days=split["gap_days"])
            folds.append({"name": f"month_{month:02d}", "train": table.index[is_train], "test": table.index[is_test]})
    else:
        raise ValueError(f"split.type không hỗ trợ: {split['type']}")
    folds = [f for f in folds if len(f["train"]) and len(f["test"])]
    for f in folds:  # chống rò rỉ: một hàng không bao giờ ở cả train lẫn test
        assert set(f["train"]).isdisjoint(f["test"])
    return folds


def train_predict(table: pd.DataFrame, features: list[str], cfg: dict,
                  fold_models: dict | None = None) -> pd.DataFrame:
    """OOF dạng dài: fold, row, subject_id, model, y_true, y_pred (+ p_<lớp> nếu phân loại).

    Nếu truyền dict `fold_models`, mô hình đã fit của từng fold được gom vào {(fold, model): estimator}.
    """
    X, y = table[features], table[cfg["target"]]
    templates = {name: build_model(spec, cfg.get("seed", 17)) for name, spec in cfg["models"].items()}
    parts = []
    for fold in make_folds(table, cfg["split"]):
        test = table.loc[fold["test"]]
        for name, template in templates.items():
            model = clone(template).fit(X.loc[fold["train"]], y.loc[fold["train"]])
            if fold_models is not None:
                fold_models[(str(fold["name"]), name)] = model
            part = pd.DataFrame({"fold": fold["name"], "row": test.index, "subject_id": test.subject_id.to_numpy(),
                                 "model": name, "y_true": test[cfg["target"]].to_numpy(),
                                 "y_pred": model.predict(test[features])})
            if cfg["kind"] == "classification":
                proba = pd.DataFrame(model.predict_proba(test[features]), columns=model.classes_)
                for c in cfg["classes"]:
                    part[f"p_{c}"] = proba[c].to_numpy() if c in proba else 0.0
            parts.append(part)
    return pd.concat(parts, ignore_index=True)


def train_final(table: pd.DataFrame, features: list[str], cfg: dict) -> dict:
    """Fit mỗi mô hình trên TOÀN BỘ dữ liệu — để dự đoán cho NGƯỜI MỚI (không có trong table).

    Không dùng dự đoán của mô hình này trên chính các hàng của `table` làm kết quả đánh giá.
    """
    X, y = table[features], table[cfg["target"]]
    return {name: build_model(spec, cfg.get("seed", 17)).fit(X, y) for name, spec in cfg["models"].items()}
