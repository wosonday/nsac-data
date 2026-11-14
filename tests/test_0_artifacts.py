import numpy as np
import pandas as pd
import pytest

from sky_ml._artifacts import load_model, save_model, write_manifest
from sky_ml._models import build_model


def _fit():
    X = pd.DataFrame({"last_value": np.arange(20.0)})
    return X, build_model({"class": "sklearn.linear_model.Ridge", "params": {"alpha": 1.0}, "scale": True}, 17).fit(
        X, np.arange(20.0) * 2)


def test_roundtrip_same_predictions(tmp_path):
    X, model = _fit()
    info = save_model(model, tmp_path / "ridge" / "final.joblib")
    write_manifest(tmp_path, [{"model": "ridge", "kind": "final", "path": "ridge/final.joblib", **info}], {})
    loaded = load_model(tmp_path, "ridge")
    assert np.allclose(loaded.predict(X), model.predict(X))
    assert not list(tmp_path.rglob("*.part"))


def test_refuses_tampered_file(tmp_path):
    _X, model = _fit()
    info = save_model(model, tmp_path / "ridge" / "final.joblib")
    write_manifest(tmp_path, [{"model": "ridge", "kind": "final", "path": "ridge/final.joblib", **info}], {})
    with open(tmp_path / "ridge" / "final.joblib", "ab") as f:
        f.write(b"x")
    with pytest.raises(ValueError, match="SHA-256"):
        load_model(tmp_path, "ridge")
