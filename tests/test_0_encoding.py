"""Chống lỗi Windows cp1252: mọi read_text/write_text trong src phải có encoding=... (hoặc đi qua _jsonio)."""
import ast
from pathlib import Path

from sky_ml._jsonio import read_json, write_json

SRC = Path(__file__).parents[1] / "src" / "sky_ml"


def test_no_text_io_without_encoding():
    bad = []
    for f in SRC.rglob("*.py"):
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("read_text", "write_text")
                    and not any(k.arg == "encoding" for k in node.keywords)):
                bad.append(f"{f.name}:{node.lineno}")
    assert not bad, f"Thiếu encoding='utf-8' tại: {bad}"


def test_json_roundtrip_vietnamese(tmp_path):
    p = write_json(tmp_path / "x.json", {"note": "chỉ dùng cho người mới — độ bao phủ"})
    assert read_json(p)["note"].startswith("chỉ dùng") and not list(tmp_path.glob("*.part"))
