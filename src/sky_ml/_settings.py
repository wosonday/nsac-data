"""Hỗ trợ (ngoài luồng): cấu hình đường dẫn và tham số — đọc từ sky_ml.yaml và configs/*.yaml."""
import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Settings:
    nasa_cl_data: Path       # nguồn NASA-cl, CHỈ ĐỌC
    data_dir: Path           # data/1_source      — bản copy (bước 1)
    features_dir: Path       # data/2_features    — dữ liệu đã xử lý / đầu vào mô hình (bước 2)
    models_dir: Path         # data/3_models      — mô hình + OOF + metric (bước 3–4)
    predictions_dir: Path    # data/4_predictions — dự đoán (bước 5)
    tasks_config: Path
    dictionary_config: Path | None = None


def load_settings(config: Path | None = None) -> Settings:
    config = Path(config or "sky_ml.yaml").resolve()
    raw = yaml.safe_load(config.read_text(encoding="utf-8"))
    base = config.parent
    source = os.environ.get("SKY_NASA_CL_DATA", raw["nasa_cl_data"])  # WSL: /mnt/d/Project/NASA-cl/data
    dictionary = raw.get("dictionary_config")
    return Settings(
        nasa_cl_data=base / source,
        data_dir=base / raw["data_dir"],
        features_dir=base / raw.get("features_dir", "data/2_features"),
        models_dir=base / raw.get("models_dir", "data/3_models"),
        predictions_dir=base / raw.get("predictions_dir", "data/4_predictions"),
        tasks_config=base / raw["tasks_config"],
        dictionary_config=base / dictionary if dictionary else None,
    )


def load_tasks(settings: Settings) -> dict[str, dict]:
    """Đọc configs/tasks.yaml → {tên task: tham số}."""
    return yaml.safe_load(settings.tasks_config.read_text(encoding="utf-8"))


def load_dictionary(settings: Settings) -> dict:
    """Đọc configs/data_dictionary.yaml (mô tả cột); không có thì trả {}."""
    path = settings.dictionary_config
    if not path or not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def ensure_writable(path: Path, settings: Settings) -> Path:
    """Chặn mọi thao tác ghi vào NASA-cl."""
    if path.resolve().is_relative_to(settings.nasa_cl_data.resolve()):
        raise ValueError(f"Không được ghi vào NASA-cl: {path}")
    return path
