from pathlib import Path

import numpy as np
import pytest

from sky_ml.cli import main
from sky_ml.copydata import copy_data
from sky_ml.prepare.windows import make_windows
from sky_ml.runs import resolve_run


def test_windows_use_only_past():
    t = make_windows(
        np.arange(40, dtype=float), np.arange(40), past=30, future=5, step=5
    )
    assert t.iloc[0].last_value == 29 and t.iloc[0].target == np.mean(
        [30, 31, 32, 33, 34]
    )


def test_window_touching_nan_is_dropped():
    v = np.arange(40, dtype=float)
    v[31] = np.nan
    assert len(make_windows(v, np.arange(40), 30, 5, 5)) == 0


def test_latest_missing_raises_hint(settings):
    with pytest.raises(FileNotFoundError, match="sky-ml prepare hr"):
        resolve_run(settings, "hr", "latest")


def test_prepare_hr_end_to_end(settings, tmp_path, monkeypatch):
    copy_data(settings)
    repo_tasks = Path(__file__).parents[1] / "configs/tasks.yaml"
    cfg = tmp_path / "sky_ml.yaml"
    cfg.write_text(
        f"nasa_cl_data: {settings.nasa_cl_data.as_posix()}\ndata_dir: data\nruns_dir: runs\n"
        f"tasks_config: {repo_tasks.as_posix()}\n"
    )
    main(["--config", str(cfg), "prepare", "hr"])
    run = resolve_run(settings, "hr")
    assert {"table.csv.gz", "features.json", "snapshot.json"} <= {
        p.name for p in run.iterdir()
    }
