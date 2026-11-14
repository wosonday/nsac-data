"""Hỗ trợ (ngoài luồng): mã run và thư mục dữ liệu của từng run.

Một `run_id` (YYYY-MM-DD_HHMMSS) được tạo ở bước 2 và đi xuyên suốt:
  data/2_features/<task>/<run_id>/      (1) dữ liệu đã xử lý — đầu vào mô hình
  data/3_models/<task>/<run_id>/        (3) mô hình đã huấn luyện + OOF + metric
  data/4_predictions/<task>/<run_id>/   (2) dự đoán từ mô hình của run đó
Không bao giờ ghi đè một run_id khác.
"""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ._settings import Settings, ensure_writable


@dataclass(frozen=True)
class RunPaths:
    task: str
    run_id: str
    features: Path
    models: Path
    predictions: Path


def run_paths(settings: Settings, task: str, run_id: str) -> RunPaths:
    return RunPaths(task, run_id, settings.features_dir / task / run_id,
                    settings.models_dir / task / run_id, settings.predictions_dir / task / run_id)


def new_run(settings: Settings, task: str) -> RunPaths:
    """Tạo run mới (thư mục features). Trùng giây thì thêm hậu tố _2, _3…"""
    base = ensure_writable(settings.features_dir / task, settings)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_id, n = stamp, 2
    while (base / run_id).exists():
        run_id, n = f"{stamp}_{n}", n + 1
    (base / run_id).mkdir(parents=True)
    return run_paths(settings, task, run_id)


def resolve_run(settings: Settings, task: str, run: str = "latest") -> RunPaths:
    base = settings.features_dir / task
    if run != "latest":
        if not (base / run).is_dir():
            raise FileNotFoundError(f"Không có run {run} trong {base}")
        return run_paths(settings, task, run)
    runs = sorted(p.name for p in base.iterdir() if p.is_dir()) if base.exists() else []
    if not runs:
        raise FileNotFoundError(f"Chưa có run cho {task}; chạy: sky-ml build-features {task}")
    return run_paths(settings, task, runs[-1])


def require(folder: Path, filename: str, step: str) -> Path:
    path = folder / filename
    if not path.exists():
        raise FileNotFoundError(f"{folder} thiếu {filename}; chạy: sky-ml {step}")
    return path
