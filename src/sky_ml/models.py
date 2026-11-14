"""Dựng mô hình sklearn từ khai báo YAML: {class, params, scale}."""
import importlib
import inspect

from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


class LastValue(BaseEstimator, RegressorMixin):
    """Baseline dự báo: giá trị sắp tới = giá trị đo cuối cùng (cột `last_value`)."""

    def __init__(self, column: str = "last_value"):
        self.column = column

    def fit(self, X, y):
        return self

    def predict(self, X):
        return X[self.column].to_numpy(dtype=float)


def build_model(spec: dict, seed: int):
    """`spec` = {class: "module.Class", params: {...}, scale: bool}. Gắn seed nếu lớp có `random_state`."""
    module, _, name = spec["class"].rpartition(".")
    cls = getattr(importlib.import_module(module), name)
    params = dict(spec.get("params") or {})
    if "random_state" in inspect.signature(cls).parameters:
        params.setdefault("random_state", seed)
    model = cls(**params)
    return make_pipeline(StandardScaler(), model) if spec.get("scale") else model
