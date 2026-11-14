import gzip
import hashlib
import json

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
    rows += [f"mmash:user_1,{60 * i},{70 + i % 5}" for i in range(80)]
    data = gzip.compress(("\n".join(rows) + "\n").encode(), mtime=0)
    (sample / "mmash_minutes.csv.gz").write_bytes(data)
    (sample / "manifest.json").write_text(json.dumps(
        {"outputs": {"mmash_minutes.csv.gz": {"sha256": hashlib.sha256(data).hexdigest()}}}))
    monkeypatch.setattr(load_data, "ALLOWLIST", ["processed/sample-v2/mmash_minutes.csv.gz",
                                                "processed/sample-v2/manifest.json"])
    return src


@pytest.fixture
def settings(tmp_path, fake_src):
    return Settings(fake_src, tmp_path / "data", tmp_path / "runs", tmp_path / "tasks.yaml")
