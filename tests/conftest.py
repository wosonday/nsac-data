import gzip
import hashlib
import json
from pathlib import Path

import pytest

from sky_ml._settings import Settings
from sky_ml._steps import load_data


@pytest.fixture
def fake_src(tmp_path, monkeypatch):
    """Cây NASA-cl giả, nhỏ: một bảng phút MMASH có hash đúng trong manifest.json."""
    src = tmp_path / "ncl"
    sample = src / "processed/sample-v2"
    sample.mkdir(parents=True)
    rows = ["subject_id,minute_start_s,hr_from_ibi_bpm_mean"]
    rows += [f"mmash:user_{u},{60 * i},{60 + 5 * u + i % 7}" for u in (1, 2, 3) for i in range(80)]
    data = gzip.compress(("\n".join(rows) + "\n").encode(), mtime=0)
    (sample / "mmash_minutes.csv.gz").write_bytes(data)
    (sample / "manifest.json").write_text(json.dumps(
        {"outputs": {"mmash_minutes.csv.gz": {"sha256": hashlib.sha256(data).hexdigest()}}}))
    monkeypatch.setattr(load_data, "ALLOWLIST", ["processed/sample-v2/mmash_minutes.csv.gz",
                                                "processed/sample-v2/manifest.json"])
    return src


@pytest.fixture
def settings(tmp_path, fake_src):
    d = tmp_path / "data"
    return Settings(fake_src, d / "1_source", d / "2_features", d / "3_models", d / "4_predictions",
                    tmp_path / "tasks.yaml")


@pytest.fixture
def config_file(tmp_path, fake_src):
    """sky_ml.yaml tạm trỏ tới NASA-cl giả + configs thật của repo (dùng cho test end-to-end qua CLI)."""
    repo = Path(__file__).parents[1]
    cfg = tmp_path / "sky_ml.yaml"
    cfg.write_text(f"nasa_cl_data: {fake_src.as_posix()}\ndata_dir: data/1_source\n"
                   "features_dir: data/2_features\nmodels_dir: data/3_models\npredictions_dir: data/4_predictions\n"
                   f"tasks_config: {(repo / 'configs/tasks.yaml').as_posix()}\n"
                   f"dictionary_config: {(repo / 'configs/data_dictionary.yaml').as_posix()}\n", encoding="utf-8")
    return cfg
