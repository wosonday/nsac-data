"""Hỗ trợ (ngoài luồng): đọc/ghi JSON luôn bằng UTF-8 và ghi nguyên tử.

Trên Windows, `Path.write_text()` mặc định dùng cp1252 → lỗi với tiếng Việt (vd. 'ộ').
Mọi file JSON của pipeline đi qua hai hàm này.
"""

import json
from pathlib import Path


def write_json(path: Path, obj) -> Path:
    """Ghi qua file .part rồi đổi tên: không bao giờ để lại file JSON rỗng/dở như khi ghi lỗi giữa chừng."""
    part = path.with_name(name=path.name + ".part")
    part.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    part.replace(path)
    return path


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
