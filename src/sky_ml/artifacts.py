"""Lưu / nạp mô hình đã huấn luyện (joblib) kèm SHA-256 và metadata để tái lập và kiểm toán.

Cảnh báo bảo mật: joblib/pickle có thể chạy mã khi nạp. Chỉ nạp file do chính pipeline tạo ra;
`load_model` từ chối file có SHA-256 khác với manifest.
"""
import hashlib
import json
import platform
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import joblib


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _versions() -> dict:
    out = {"python": platform.python_version()}
    for name in ("scikit-learn", "lightgbm", "numpy", "joblib"):
        try:
            out[name] = version(name)
        except PackageNotFoundError:
            out[name] = None
    return out


def save_model(model, path: Path) -> dict:
    """Ghi qua file .part rồi đổi tên (không để file dở); trả {file, bytes, sha256}."""
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    joblib.dump(model, part, compress=3)
    part.replace(path)
    return {"file": path.name, "bytes": path.stat().st_size, "sha256": _sha256(path)}


def write_manifest(models_dir: Path, entries: list[dict], context: dict) -> Path:
    manifest = {"versions": _versions(), **context, "models": entries}
    path = models_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return path


def load_model(models_dir: Path, name: str, kind: str = "final"):
    """Nạp mô hình `name` (kind = 'final' hoặc tên fold) sau khi kiểm SHA-256 theo manifest."""
    manifest = json.loads((models_dir / "manifest.json").read_text())
    entry = next((m for m in manifest["models"] if m["model"] == name and m["kind"] == kind), None)
    if entry is None:
        raise FileNotFoundError(f"Không có mô hình {name}/{kind} trong {models_dir / 'manifest.json'}")
    path = models_dir / entry["path"]
    if _sha256(path) != entry["sha256"]:
        raise ValueError(f"SHA-256 lệch manifest, từ chối nạp: {path}")
    return joblib.load(path)
