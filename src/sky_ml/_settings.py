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
