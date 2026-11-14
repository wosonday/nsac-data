"""Hỗ trợ (ngoài luồng): SHA-256 file và tên manifest bản copy, dùng chung cho bước 1 và 2."""
import hashlib
from pathlib import Path

MANIFEST_NAME = "COPY_MANIFEST.csv"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
