import pandas as pd
from sklearn.pipeline import Pipeline

from sky_ml._models import LastValue, build_model


def test_build_ridge_with_scaling():
    m = build_model({"class": "sklearn.linear_model.Ridge", "params": {"alpha": 1.0}, "scale": True}, seed=17)
    assert isinstance(m, Pipeline) and m.steps[-1][1].alpha == 1.0


def test_seed_injected_when_supported():
    m = build_model({"class": "lightgbm.LGBMRegressor", "params": {"n_estimators": 5}}, seed=17)
    assert m.random_state == 17


def test_last_value_predicts_column():
    X = pd.DataFrame({"last_value": [70.0, 80.0], "other": [1, 2]})
    assert list(LastValue().fit(X, None).predict(X)) == [70.0, 80.0]
