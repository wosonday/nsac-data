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
