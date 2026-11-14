"""Thư mục kết quả runs/<task>/<run_id>/; không bao giờ ghi đè."""
from datetime import datetime
from pathlib import Path

from ._settings import Settings, ensure_writable


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
        raise FileNotFoundError(f"Chưa có run cho {task}; chạy: sky-ml build-features {task}")
    return runs[-1]


def require(run_dir: Path, filename: str, step: str) -> Path:
    path = run_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"{run_dir} thiếu {filename}; chạy: sky-ml {step}")
    return path
