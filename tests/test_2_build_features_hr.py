from pathlib import Path

import numpy as np
import pytest

from sky_ml._cli import main
from sky_ml._steps import load_data

copy_data = load_data.copy_data
from sky_ml._steps import build_features

W = build_features.windows
NAMES = list(W.FEATURES)[:7]
from sky_ml._runs import resolve_run


def test_windows_use_only_past():
    t = W.make_windows(np.arange(40, dtype=float), np.arange(40), past=30, future=5, step=5, names=NAMES)
    assert t.iloc[0].last_value == 29 and t.iloc[0].target == np.mean([30, 31, 32, 33, 34])


def test_window_touching_nan_is_dropped():
    v = np.arange(40, dtype=float)
    v[31] = np.nan
    assert len(W.make_windows(v, np.arange(40), 30, 5, 5, NAMES)) == 0


def test_latest_missing_raises_hint(settings):
    with pytest.raises(FileNotFoundError, match="sky-ml build-features hr"):
        resolve_run(settings, "hr", "latest")


def test_prepare_hr_end_to_end(settings, tmp_path, monkeypatch):
    copy_data(settings)
    repo_tasks = Path(__file__).parents[1] / "configs/tasks.yaml"
    cfg = tmp_path / "sky_ml.yaml"
    cfg.write_text(f"nasa_cl_data: {settings.nasa_cl_data.as_posix()}\ndata_dir: data\nruns_dir: runs\n"
                   f"tasks_config: {repo_tasks.as_posix()}\n")
    main(["--config", str(cfg), "build-features", "hr"])
    run = resolve_run(settings, "hr")
    assert {"2_table.csv.gz", "2_features.json", "2_snapshot.json"} <= {p.name for p in run.iterdir()}


def test_unknown_feature_in_config_rejected():
    import pytest
    with pytest.raises(ValueError, match="không tồn tại"):
        W.check_features(["last_value", "khong_co"])


def test_feature_selection_follows_config():
    t = W.make_windows(np.arange(40, dtype=float), np.arange(40), 30, 5, 5, ["last_value", "slope_all"])
    assert list(t.columns) == ["cutoff_time", "last_value", "slope_all", "target"]
    assert t.iloc[0].slope_all == pytest.approx(1.0)
