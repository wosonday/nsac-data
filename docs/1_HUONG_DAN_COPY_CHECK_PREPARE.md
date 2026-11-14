# Hướng dẫn build `sky-ml`: copy dữ liệu và preprocess ban đầu

> **Cập nhật 14/11 14:10, quy ước đặt tên.** Bước pipeline được đánh số theo thứ tự chạy; file hỗ trợ (ngoài luồng) có tiền tố `_`. Trong tài liệu này, tên cũ tương ứng với tên mới như sau:
> - `copydata.py` → `1_copydata.py`
> - `datacheck.py` → `2_datacheck.py`
> - `prepare/` → `3_prepare/`
> - `train.py` → `4_train.py`
> - `evaluate.py` → `5_evaluate.py`
> - `settings.py` → `_settings.py`; `runs.py` → `_runs.py`; `models.py` → `_models.py`; `artifacts.py` → `_artifacts.py`; `cli.py` → `_cli.py`
> - mới: `_hashing.py`, `_steps.py`
>
> File trong `runs/<task>/<run>/` mang số của bước tạo ra nó: `3_snapshot.json`, `3_table.csv.gz`, `3_features.json`; `4_oof.csv.gz`, `4_folds.json`, `4_models/`; `5_metrics.csv`, `5_summary.json`.
>
> Lệnh `sky-ml …` giữ nguyên. Lệnh mới `uv run sky-ml steps` in thứ tự các bước. **Code trong phần phụ lục của tài liệu này là bản trước khi đổi tên; bản đúng là các file trong `src/`.**


Áp dụng cho Task 1–4 của kế hoạch `docs/superpowers/plans/2026-11-14-sky-ml.md`. Mọi lệnh chạy trong **PowerShell**, tại `D:\Project\nasa-hackathon`.

Mã nguồn dưới đây đã được kiểm tra trước với dữ liệu thật của NASA-cl:
- 37 file, 496,3 MB;
- 25 file có hash do NASA-cl công bố đều khớp (20 file EDF của Sleep-EDF, 2 file sample-v2, 3 CSV Lidal);
- `prepare hr` cho **5.301 cửa sổ, 22 người**, trùng run ngày 11/11;
- 14/14 test đạt, `ruff` sạch.

## Bước 0. Cài công cụ (một lần)

**Ý nghĩa:** `uv` tự tải Python 3.12 và quản lý thư viện, nên không ảnh hưởng tới Python sẵn có trên máy.

```powershell
winget install --id=astral-sh.uv -e      # hoặc: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
winget install --id=Git.Git -e           # nếu chưa có git
cd D:\Project\nasa-hackathon
git init
```

## Bước 1. Tạo cây thư mục

```powershell
mkdir src\sky_ml\prepare, tests, configs
```

Kết quả sau khi tạo đủ file ở bước 2:

```text
nasa-hackathon/
├── pyproject.toml  .python-version  .gitignore  sky_ml.yaml
├── configs/  tasks.yaml
├── src/sky_ml/  __init__.py settings.py copydata.py datacheck.py runs.py cli.py
│   └── prepare/ __init__.py windows.py hr.py
└── tests/  conftest.py test_settings.py test_copydata.py test_datacheck.py test_prepare_hr.py
```

## Bước 2. Tạo các file (theo thứ tự)

| File | Vai trò | Vì sao cần |
|---|---|---|
| `pyproject.toml`, `.python-version` | Khai báo môi trường | Ghim sklearn 1.9.1 và LightGBM 4.7.0 để tái lập kết quả 11/11 |
| `sky_ml.yaml` | Đường dẫn nguồn, đích, file tham số task | Đổi máy hoặc WSL chỉ cần sửa file này hoặc biến `SKY_NASA_CL_DATA` |
| `configs/tasks.yaml` | Tham số từng task (cửa sổ, target, cách chia tập…) | Mọi tham số nằm ở YAML, sửa không cần đụng code |
| `settings.py` | Đọc 2 file YAML, chặn ghi vào NASA-cl | Bảo vệ dữ liệu gốc |
| `copydata.py` | Copy theo allowlist, kiểm SHA-256, ghi `COPY_MANIFEST.csv` | Copy an toàn: chạy lại được, không để file dở |
| `datacheck.py` | Kiểm bản copy; tạo `snapshot.json` | Biết chắc mỗi run tính từ đúng dữ liệu nào |
| `runs.py` | Tạo `runs/<task>/<thời điểm>/` | Không ghi đè kết quả cũ |
| `prepare/windows.py`, `prepare/hr.py` | Cắt cửa sổ 30 phút → HR 5 phút tới | Đặc trưng chỉ lấy từ quá khứ (chống rò rỉ) |
| `cli.py` | Lệnh `sky-ml copy-data / check / prepare` | Chạy riêng từng bước |
| `tests/*` | Test bằng dữ liệu giả nhỏ | Kiểm tra logic mà không cần dữ liệu thật |

### `pyproject.toml`

```toml
[project]
name = "sky-ml"
version = "0.1.0"
requires-python = ">=3.12,<3.14"
dependencies = [
    "numpy>=2.1",
    "pandas>=2.2",
    "scipy>=1.14",
    "scikit-learn==1.9.1",
    "lightgbm==4.7.0",
    "mne>=1.8",
    "shap>=0.46",
    "matplotlib>=3.9",
    "pyyaml>=6.0",
]

[dependency-groups]
dev = ["pytest>=8.3", "ruff>=0.8"]

[project.scripts]
sky-ml = "sky_ml.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/sky_ml"]

[tool.pytest.ini_options]
markers = ["slow: cần dữ liệu thật"]
addopts = "-m 'not slow'"
```

### `.python-version`

```text
3.12
```

### `.gitignore`

```text
data/
runs/
.venv/
__pycache__/
*.egg-info
```

### `sky_ml.yaml`

```yaml
# Cấu hình chung. Đường dẫn tương đối tính theo thư mục chứa file này.
nasa_cl_data: D:/Project/NASA-cl/data   # nguồn, CHỈ ĐỌC (ghi đè bằng env SKY_NASA_CL_DATA)
data_dir: data                          # bản copy
runs_dir: runs                          # kết quả từng lần chạy
tasks_config: configs/tasks.yaml        # tham số từng task
```

### `configs/tasks.yaml`

```yaml
# Tham số từng task — giá trị chép từ NASA-cl/src/nasa_cl/pipeline/config.py (run 2026-11-11).
# Mô hình (models) sẽ được thêm ở bước train.
hr:
  description: "MMASH (22 người, mặt đất): HR trung bình 5 phút tới từ 30 phút trước"
  inputs:
    - processed/sample-v2/mmash_minutes.csv.gz
  kind: regression
  target: hr_next_5min
  unit: bpm
  window: {past: 30, future: 5, step: 5}     # đơn vị: phút
  valid_hr_range: [30.0, 220.0]              # ngưỡng kỹ thuật loại số đo hỏng, KHÔNG phải ngưỡng lâm sàng
  split: {type: leave_one_subject_out}
  baseline: last_value
```

### `src/sky_ml/__init__.py`

```python
# (file rỗng)
```

### `src/sky_ml/settings.py`

```python
"""Cấu hình: nguồn NASA-cl (chỉ đọc), data (bản copy), runs (kết quả), file tham số task — đọc từ YAML."""
import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Settings:
    nasa_cl_data: Path
    data_dir: Path
    runs_dir: Path
    tasks_config: Path


def load_settings(config: Path | None = None) -> Settings:
    config = Path(config or "sky_ml.yaml").resolve()
    raw = yaml.safe_load(config.read_text(encoding="utf-8"))
    base = config.parent
    source = os.environ.get("SKY_NASA_CL_DATA", raw["nasa_cl_data"])  # WSL: /mnt/d/Project/NASA-cl/data
    return Settings(base / source, base / raw["data_dir"], base / raw["runs_dir"], base / raw["tasks_config"])


def load_tasks(settings: Settings) -> dict[str, dict]:
    """Đọc configs/tasks.yaml → {tên task: tham số}."""
    return yaml.safe_load(settings.tasks_config.read_text(encoding="utf-8"))


def ensure_writable(path: Path, settings: Settings) -> Path:
    """Chặn mọi thao tác ghi vào NASA-cl."""
    if path.resolve().is_relative_to(settings.nasa_cl_data.resolve()):
        raise ValueError(f"Không được ghi vào NASA-cl: {path}")
    return path
```

### `src/sky_ml/copydata.py`

```python
"""Bước 0: copy đúng các file 4 task cần từ NASA-cl sang data/, kiểm SHA-256, ghi COPY_MANIFEST.csv."""
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from .settings import Settings, ensure_writable

MANIFEST_NAME = "COPY_MANIFEST.csv"

# Đường dẫn/glob tương đối trong NASA-cl/data
ALLOWLIST = [
    "raw/nlsp/MR080G.zip", "raw/nlsp/MR079G.zip", "raw/nlsp/BRSMImmune.zip",   # cpet
    "raw/nlsp/download_manifest.csv",
    "raw/sleep_edfx/1.0.0/sleep-cassette/SC40?1*-PSG.edf",                       # sleep
    "raw/sleep_edfx/1.0.0/sleep-cassette/SC40?1*-Hypnogram.edf",
    "raw/sleep_edfx/1.0.0/download_manifest.csv",
    "raw/sleep_edfx/1.0.0/LICENSE.html", "raw/sleep_edfx/1.0.0/SHA256SUMS.txt",
    "processed/sample-v2/mmash_minutes.csv.gz",                                  # hr
    "processed/sample-v2/manifest.json", "processed/sample-v2/quality_report.md",
    "raw/mmash/1.0.0/LICENSE.txt",
    "raw/radlab/instruments/Lidal/*.csv", "raw/radlab/instruments/Lidal/*.csv.meta.json",  # dose
]


@dataclass(frozen=True)
class CopyItem:
    rel_path: str
    expected_sha256: str | None
    hash_source: str  # "nasa_cl_manifest" | "computed"


def _known_hashes(src: Path) -> dict[str, str]:
    """Hash do chính NASA-cl công bố: manifest Sleep-EDF, manifest sample-v2, sidecar RadLab."""
    known = {}
    sleep = src / "raw/sleep_edfx/1.0.0/download_manifest.csv"
    if sleep.exists():
        for row in pd.read_csv(sleep).itertuples():
            known[f"raw/sleep_edfx/1.0.0/{row.file_name}"] = row.local_sha256
    sample = src / "processed/sample-v2/manifest.json"
    if sample.exists():
        for name, meta in json.loads(sample.read_text(encoding="utf-8"))["outputs"].items():
            known[f"processed/sample-v2/{name}"] = meta["sha256"]
    for meta in (src / "raw/radlab/instruments/Lidal").glob("*.csv.meta.json"):
        known[meta.relative_to(src).as_posix().removesuffix(".meta.json")] = json.loads(meta.read_text())["sha256"]
    return known


def build_allowlist(src: Path) -> list[CopyItem]:
    known, items = _known_hashes(src), []
    for pattern in ALLOWLIST:
        matches = sorted(src.glob(pattern))
        if not matches:
            raise FileNotFoundError(f"Thiếu trong NASA-cl: {pattern}")
        for path in matches:
            rel = path.relative_to(src).as_posix()
            sha = known.get(rel)
            items.append(CopyItem(rel, sha, "nasa_cl_manifest" if sha else "computed"))
    return items


def _copy_one(src: Path, dst: Path) -> str:
    """Copy qua file .part rồi đổi tên: không bao giờ để file dở dang ở đích."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    part, h = dst.with_name(dst.name + ".part"), hashlib.sha256()
    try:
        with open(src, "rb") as fin, open(part, "wb") as fout:
            for chunk in iter(lambda: fin.read(1 << 20), b""):
                h.update(chunk)
                fout.write(chunk)
        os.replace(part, dst)
    finally:
        part.unlink(missing_ok=True)
    return h.hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_data(settings: Settings, dry_run: bool = False) -> pd.DataFrame:
    src, dst_root = settings.nasa_cl_data, ensure_writable(settings.data_dir, settings)
    items = build_allowlist(src)
    if dry_run:
        size = sum((src / i.rel_path).stat().st_size for i in items)
        print(f"Sẽ copy {len(items)} file, {size / 2**20:.1f} MB từ {src}")
        return pd.DataFrame([i.__dict__ for i in items])

    old = {}
    if (dst_root / MANIFEST_NAME).exists():
        old = pd.read_csv(dst_root / MANIFEST_NAME).set_index("rel_path").sha256.to_dict()
    rows = []
    for item in items:
        source, target = src / item.rel_path, dst_root / item.rel_path
        expected = item.expected_sha256 or old.get(item.rel_path)
        if target.exists() and expected and sha256_file(target) == expected:
            sha, status = expected, "skipped_ok"
        else:
            sha, status = _copy_one(source, target), "copied"
            if item.expected_sha256 and sha != item.expected_sha256:
                target.unlink()
                raise ValueError(f"sha256 lệch manifest NASA-cl: {item.rel_path}")
        rows.append({"rel_path": item.rel_path, "bytes": target.stat().st_size, "sha256": sha,
                     "hash_source": item.hash_source, "status": status,
                     "copied_at_utc": datetime.now(UTC).isoformat(timespec="seconds")})
    table = pd.DataFrame(rows)
    table.to_csv(dst_root / MANIFEST_NAME, index=False)
    return table
```

### `src/sky_ml/datacheck.py`

```python
"""Bước 1: bản copy trong data/ còn khớp COPY_MANIFEST.csv không; snapshot cho mỗi run."""
import platform
from importlib.metadata import PackageNotFoundError, version

import pandas as pd

from .copydata import MANIFEST_NAME, sha256_file
from .settings import Settings

LIBRARIES = ["scikit-learn", "lightgbm", "pandas", "numpy", "scipy", "mne", "shap"]


def verify_copy(settings: Settings, rel_paths: list[str] | None = None) -> int:
    manifest_path = settings.data_dir / MANIFEST_NAME
    if not manifest_path.exists():
        raise FileNotFoundError("Chưa có data/COPY_MANIFEST.csv; chạy: sky-ml copy-data")
    manifest = pd.read_csv(manifest_path).set_index("rel_path")
    wanted = rel_paths if rel_paths is not None else list(manifest.index)
    problems = []
    for rel in wanted:
        path = settings.data_dir / rel
        if rel not in manifest.index or not path.exists():
            problems.append(f"thiếu: {rel}")
        elif sha256_file(path) != manifest.loc[rel, "sha256"]:
            problems.append(f"đã bị sửa: {rel}")
    if problems:
        raise ValueError("Dữ liệu không khớp COPY_MANIFEST:\n  " + "\n  ".join(problems))
    return len(wanted)


def _version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def snapshot(settings: Settings, rel_paths: list[str]) -> dict:
    manifest = pd.read_csv(settings.data_dir / MANIFEST_NAME).set_index("rel_path")
    return {"files": {rel: manifest.loc[rel, "sha256"] for rel in rel_paths},
            "python": platform.python_version(),
            "libraries": {name: _version(name) for name in LIBRARIES},
            "seed": 17}
```

### `src/sky_ml/runs.py`

```python
"""Thư mục kết quả runs/<task>/<run_id>/; không bao giờ ghi đè."""
from datetime import datetime
from pathlib import Path

from .settings import Settings, ensure_writable


def new_run(settings: Settings, task: str) -> Path:
    base = ensure_writable(settings.runs_dir / task, settings)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run, n = base / stamp, 2
    while run.exists():
        run, n = base / f"{stamp}_{n}", n + 1
    run.mkdir(parents=True)
    return run


def resolve_run(settings: Settings, task: str, run: str = "latest") -> Path:
    base = settings.runs_dir / task
    if run != "latest":
        return base / run
    runs = sorted(p for p in base.glob("*") if p.is_dir()) if base.exists() else []
    if not runs:
        raise FileNotFoundError(f"Chưa có run cho {task}; chạy: sky-ml prepare {task}")
    return runs[-1]


def require(run_dir: Path, filename: str, step: str) -> Path:
    path = run_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"{run_dir} thiếu {filename}; chạy: sky-ml {step}")
    return path
```

### `src/sky_ml/prepare/windows.py`

```python
"""Cắt chuỗi đều thành cửa sổ: `past` điểm quá khứ → trung bình `future` điểm kế tiếp."""
import numpy as np
import pandas as pd

WINDOW_FEATURES = ["last_value", "mean_last_5", "mean_all", "std_all", "change_last_10", "min_all", "max_all"]


def make_windows(values, times, past: int, future: int, step: int) -> pd.DataFrame:
    rows = []
    for end in range(past, len(values) - future + 1, step):
        x, y = values[end - past:end], values[end:end + future]   # đặc trưng chỉ từ quá khứ
        if np.isnan(x).any() or np.isnan(y).any():                # không nội suy qua chỗ thiếu
            continue
        rows.append({"cutoff_time": times[end - 1], "last_value": x[-1], "mean_last_5": x[-5:].mean(),
                     "mean_all": x.mean(), "std_all": x.std(), "change_last_10": x[-1] - x[-10],
                     "min_all": x.min(), "max_all": x.max(), "target": y.mean()})
    return pd.DataFrame(rows)
```

### `src/sky_ml/prepare/hr.py`

```python
"""MMASH (sample-v2) → một hàng / cửa sổ 30 phút của một người."""
from pathlib import Path

import numpy as np
import pandas as pd

from .windows import WINDOW_FEATURES, make_windows


def prepare_hr(data_dir: Path, cfg: dict) -> tuple[pd.DataFrame, list[str]]:
    minutes = pd.read_csv(data_dir / cfg["inputs"][0],
                          usecols=["subject_id", "minute_start_s", "hr_from_ibi_bpm_mean"])
    low, high, w = *cfg["valid_hr_range"], cfg["window"]
    parts = []
    for subject_id, person in minutes.groupby("subject_id"):
        minute = (person.minute_start_s // 60).astype(int).to_numpy()
        hr = person.hr_from_ibi_bpm_mean.to_numpy(dtype=float, copy=True)
        hr[(hr < low) | (hr > high)] = np.nan                         # số đo không khả dĩ → thiếu
        grid = np.full(minute.max() - minute.min() + 1, np.nan)        # lưới 1 phút, phút vắng = NaN
        grid[minute - minute.min()] = hr
        windows = make_windows(grid, np.arange(len(grid)), w["past"], w["future"], w["step"])
        if len(windows):
            windows.insert(0, "subject_id", subject_id)
            parts.append(windows)
    table = pd.concat(parts, ignore_index=True).rename(columns={"target": cfg["target"]})
    return table, WINDOW_FEATURES
```

### `src/sky_ml/prepare/__init__.py`

```python
from .hr import prepare_hr

PREPARE = {"hr": prepare_hr}
```

### `src/sky_ml/cli.py`

```python
"""sky-ml copy-data | check | prepare <task>"""
import argparse
import json

from .copydata import copy_data
from .datacheck import snapshot, verify_copy
from .prepare import PREPARE
from .runs import new_run
from .settings import load_settings, load_tasks


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sky-ml")
    parser.add_argument("--config", default="sky_ml.yaml")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("copy-data").add_argument("--dry-run", action="store_true")
    sub.add_parser("check")
    sub.add_parser("prepare").add_argument("task", choices=sorted(PREPARE))
    args = parser.parse_args(argv)
    settings = load_settings(args.config)

    if args.command == "copy-data":
        table = copy_data(settings, dry_run=args.dry_run)
        if not args.dry_run:
            print(table.status.value_counts().to_string(), f"\n→ {settings.data_dir}")
    elif args.command == "check":
        print(f"OK {verify_copy(settings)} files")
    elif args.command == "prepare":
        cfg = load_tasks(settings)[args.task]
        verify_copy(settings, cfg["inputs"])
        table, features = PREPARE[args.task](settings.data_dir, cfg)
        run = new_run(settings, args.task)
        table.to_csv(run / "table.csv.gz", index=False)
        (run / "features.json").write_text(json.dumps(features, indent=2))
        (run / "snapshot.json").write_text(json.dumps(snapshot(settings, cfg["inputs"]), indent=2))
        print(f"{args.task}: {len(table)} hàng, {table.subject_id.nunique()} người → {run}")


if __name__ == "__main__":
    main()
```

### `tests/conftest.py`

```python
import gzip
import hashlib
import json

import pytest

from sky_ml import copydata
from sky_ml.settings import Settings


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
    monkeypatch.setattr(copydata, "ALLOWLIST", ["processed/sample-v2/mmash_minutes.csv.gz",
                                                "processed/sample-v2/manifest.json"])
    return src


@pytest.fixture
def settings(tmp_path, fake_src):
    return Settings(fake_src, tmp_path / "data", tmp_path / "runs", tmp_path / "tasks.yaml")
```

### `tests/test_settings.py`

```python
import pytest

from sky_ml.settings import Settings, ensure_writable, load_settings, load_tasks


def test_env_overrides_source(tmp_path, monkeypatch):
    cfg = tmp_path / "sky_ml.yaml"
    cfg.write_text("nasa_cl_data: X\ndata_dir: data\nruns_dir: runs\ntasks_config: configs/tasks.yaml\n")
    monkeypatch.setenv("SKY_NASA_CL_DATA", str(tmp_path / "src"))
    s = load_settings(cfg)
    assert s.nasa_cl_data == tmp_path / "src" and s.data_dir == tmp_path / "data"
    assert s.tasks_config == tmp_path / "configs/tasks.yaml"


def test_refuses_output_inside_source(tmp_path):
    s = Settings(tmp_path / "ncl", tmp_path / "data", tmp_path / "runs", tmp_path / "t.yaml")
    with pytest.raises(ValueError, match="NASA-cl"):
        ensure_writable(tmp_path / "ncl" / "runs", s)


def test_repo_tasks_yaml_is_valid():
    """configs/tasks.yaml của repo phải đọc được và có đủ khóa bắt buộc."""
    from pathlib import Path
    s = load_settings(Path(__file__).parents[1] / "sky_ml.yaml")
    hr = load_tasks(s)["hr"]
    assert hr["window"] == {"past": 30, "future": 5, "step": 5} and hr["valid_hr_range"] == [30.0, 220.0]
```

### `tests/test_copydata.py`

```python

import pytest

from sky_ml import copydata
from sky_ml.copydata import copy_data


def test_copies_and_verifies(settings):
    df = copy_data(settings)
    assert set(df.status) == {"copied"}
    assert df.set_index("rel_path").loc["processed/sample-v2/mmash_minutes.csv.gz", "hash_source"] == "nasa_cl_manifest"


def test_second_run_skips(settings):
    copy_data(settings)
    assert set(copy_data(settings).status) == {"skipped_ok"}


def test_hash_mismatch_removes_dst(settings, fake_src):
    (fake_src / "processed/sample-v2/mmash_minutes.csv.gz").write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="sha256"):
        copy_data(settings)
    assert not any(settings.data_dir.rglob("*.csv.gz"))


def test_copy_interrupted_leaves_no_partial(settings, monkeypatch):
    def boom(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(copydata.os, "replace", boom)
    with pytest.raises(OSError):
        copy_data(settings)
    assert not [p for p in settings.data_dir.rglob("*") if p.is_file()]


def test_dry_run_writes_nothing(settings):
    copy_data(settings, dry_run=True)
    assert not settings.data_dir.exists()
```

### `tests/test_datacheck.py`

```python
import pytest

from sky_ml.copydata import copy_data
from sky_ml.datacheck import verify_copy

REL = "processed/sample-v2/mmash_minutes.csv.gz"


def test_check_passes_after_copy(settings):
    copy_data(settings)
    assert verify_copy(settings) == 2


def test_check_detects_modified_file(settings):
    copy_data(settings)
    with open(settings.data_dir / REL, "ab") as f:
        f.write(b"x")
    with pytest.raises(ValueError, match="mmash_minutes"):
        verify_copy(settings)
```

### `tests/test_prepare_hr.py`

```python
from pathlib import Path

import numpy as np
import pytest

from sky_ml.cli import main
from sky_ml.copydata import copy_data
from sky_ml.prepare.windows import make_windows
from sky_ml.runs import resolve_run


def test_windows_use_only_past():
    t = make_windows(np.arange(40, dtype=float), np.arange(40), past=30, future=5, step=5)
    assert t.iloc[0].last_value == 29 and t.iloc[0].target == np.mean([30, 31, 32, 33, 34])


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
    cfg.write_text(f"nasa_cl_data: {settings.nasa_cl_data.as_posix()}\ndata_dir: data\nruns_dir: runs\n"
                   f"tasks_config: {repo_tasks.as_posix()}\n")
    main(["--config", str(cfg), "prepare", "hr"])
    run = resolve_run(settings, "hr")
    assert {"table.csv.gz", "features.json", "snapshot.json"} <= {p.name for p in run.iterdir()}
```

## Bước 3. Cài môi trường và chạy test

```powershell
uv sync                 # tạo .venv, cài Python 3.12 và thư viện (lần đầu mất vài phút)
uv run pytest -v        # kỳ vọng: 14 passed
uv run ruff check src tests
```

Nếu `uv sync` báo không tìm thấy bản `scikit-learn==1.9.1` cho máy: chạy `uv python pin 3.12` rồi `uv sync` lại. Không nới phiên bản, vì sẽ mất khả năng tái lập kết quả.

## Đổi tham số

Mọi tham số nằm trong YAML:
- Đổi đường dẫn: sửa `sky_ml.yaml`.
- Đổi cửa sổ HR, ví dụ 60 → 10 phút: sửa `configs/tasks.yaml` → `hr.window`, rồi chạy lại `uv run sky-ml prepare hr`. Run mới tạo thư mục mới, run cũ giữ nguyên để so sánh.
- Dùng một bộ cấu hình khác: `uv run sky-ml --config sky_ml_wsl.yaml check`.

## Bước 4. Copy dữ liệu

```powershell
uv run sky-ml copy-data --dry-run   # kỳ vọng: "Sẽ copy 37 file, 496.3 MB từ D:\Project\NASA-cl\data"
uv run sky-ml copy-data             # kỳ vọng: copied 37
uv run sky-ml copy-data             # chạy lại: skipped_ok 37 (an toàn)
uv run sky-ml check                 # kỳ vọng: OK 37 files
```

**Cách đọc kết quả:**
- Mở `data\COPY_MANIFEST.csv`. Cột `hash_source = nasa_cl_manifest` (25 file) nghĩa là hash đã được đối chiếu với công bố của NASA-cl.
- Cột `hash_source = computed` (12 file: ZIP UTMB, manifest, license, sidecar) nghĩa là hash được tính lúc copy. Hash từng CSV bên trong ZIP UTMB sẽ được kiểm lại ở bước `prepare cpet`.

**Lỗi thường gặp:**

| Thông báo | Nguyên nhân | Cách xử lý |
|---|---|---|
| `Thiếu trong NASA-cl: ...` | Sai đường dẫn nguồn | Sửa `nasa_cl_data` trong `sky_ml.yaml` |
| `sha256 lệch manifest NASA-cl` | File gốc bị đổi hoặc hỏng | Kiểm tra lại file đó trong NASA-cl; không ép copy |
| `Không được ghi vào NASA-cl` | `data_dir` hoặc `runs_dir` trỏ vào NASA-cl | Đặt lại về `data` và `runs` |
| `Dữ liệu không khớp COPY_MANIFEST` | File trong `data\` đã bị sửa | Xóa file đó rồi chạy lại `copy-data` |

Khi chạy trong WSL: `export SKY_NASA_CL_DATA=/mnt/d/Project/NASA-cl/data` trước khi chạy lệnh.

## Bước 5. Preprocess ban đầu (task `hr`)

```powershell
uv run sky-ml prepare hr
# kỳ vọng: hr: 5301 hàng, 22 người → D:\Project\nasa-hackathon\runs\hr\<thời điểm>
```

**Cách đọc kết quả** (mở `runs\hr\<thời điểm>\`):
- `table.csv.gz`: mỗi hàng là một cửa sổ 30 phút của một người.
  - `cutoff_time` là phút cuối của cửa sổ.
  - Bảy đặc trưng (`last_value`, `mean_last_5`, `mean_all`, `std_all`, `change_last_10`, `min_all`, `max_all`) chỉ tính từ quá khứ.
  - `hr_next_5min` là target: HR trung bình 5 phút tiếp theo.
  - Hàng đầu (`mmash:user_1`, `cutoff_time = 29`) có `hr_next_5min = 94.16`, trùng `y_true` trong OOF 11/11.
- `features.json`: danh sách cột mô hình được phép dùng.
- `snapshot.json`: SHA-256 của file đầu vào, phiên bản Python và thư viện, seed.

**Ví dụ kiểm tra nhanh bằng Python:**

```powershell
uv run python -c "import pandas as pd, glob; t=pd.read_csv(sorted(glob.glob('runs/hr/*/table.csv.gz'))[-1]); print(t.groupby('subject_id').size().describe())"
```

## Bước 6. Commit

```powershell
git add .
git commit -m "feat: copy-data, check, prepare hr"
```

## Bước tiếp theo

Theo kế hoạch: Task 5 (`train`), Task 6 (`evaluate` + tái lập HR MAE 3,9174), rồi `dose`, `cpet`, `sleep`.
