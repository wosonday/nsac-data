"""Hỗ trợ (ngoài luồng): sinh tài liệu cho từng thư mục dữ liệu và sổ danh mục toàn bộ dữ liệu.

- write_card(...)  → <thư mục>/README.md   (data card: là gì, từ đâu, cột/đơn vị, giới hạn, cách đọc)
- register(...)    → data/CATALOG.csv       (mỗi artifact một dòng: loại, task, run, đường dẫn, số hàng, sha256)
                     + cập nhật mục danh mục trong data/README.md (giữa hai marker CATALOG:START/END)
"""
import csv
import re
from datetime import UTC, datetime
from pathlib import Path

from ._hashing import sha256_file

CATALOG_FIELDS = ["created_at_utc", "kind", "task", "run_id", "path", "rows", "bytes", "sha256", "produced_by"]


def _column_info(c: str, known: dict, patterns: dict) -> dict:
    """Tra cột: tên chính xác (task ghi đè chung) → mẫu regex (vd. ^(fpz|pz|eog)_delta) → rỗng."""
    if c in known:
        return known[c]
    for pat, info in patterns.items():
        m = re.fullmatch(pat, c)
        if m:
            return {**info, "description": info.get("description", "").format(*m.groups())}
    return {}


def _column_rows(columns: list[str], dictionary: dict, unit: str | None, task: str = "") -> list[str]:
    tinfo = dictionary.get("tasks", {}).get(task, {})
    known = {**dictionary.get("columns", {}), **tinfo.get("columns", {})}
    patterns = dictionary.get("column_patterns", {})
    lines = ["| Cột | Đơn vị | Ý nghĩa |", "|---|---|---|"]
    for c in columns:
        info = _column_info(c, known, patterns)
        u = str(info.get("unit", "")).replace("{unit}", unit or "")
        lines.append(f"| `{c}` | {u} | {info.get('description', '(chưa mô tả trong data_dictionary.yaml)')} |")
    return lines


def write_card(folder: Path, kind: str, task: str, run_id: str, dictionary: dict, *, unit: str | None,
               produced_by: str, files: dict[str, str], columns: list[str] | None = None,
               facts: dict | None = None, lineage: dict[str, str] | None = None, extra: list[str] | None = None
               ) -> Path:
    """Ghi folder/README.md. `files` = {tên file: mô tả}; `facts` = số liệu chính (số hàng, người, metric…)."""
    meta = dictionary.get("kinds", {}).get(kind, {})
    tinfo = dictionary.get("tasks", {}).get(task, {})
    lines = [f"# {meta.get('title', kind)} — `{task}` / run `{run_id}`", "",
             meta.get("purpose", ""), "",
             f"- **Tạo bởi:** `{produced_by}`",
             f"- **README cập nhật (UTC):** {datetime.now(UTC).isoformat(timespec='seconds')}"]
    if tinfo.get("cohort"):
        lines.append(f"- **Cohort:** {tinfo['cohort']}")
    if tinfo.get("source"):
        lines.append(f"- **Nguồn:** {tinfo['source']}")
    lines += ["", "## File trong thư mục", "", "| File | Nội dung |", "|---|---|"]
    lines += [f"| `{f}` | {d} |" for f, d in files.items()]
    lines = [ln.replace("\n", " ") for ln in lines]
    if facts:
        lines += ["", "## Số liệu chính", "", "| Chỉ tiêu | Giá trị |", "|---|---|"]
        lines += [f"| {k} | {v} |" for k, v in facts.items()]
    if columns:
        lines += ["", "## Cột dữ liệu", "", *_column_rows(columns, dictionary, unit, task)]
    if lineage:
        lines += ["", "## Truy vết (lineage)", ""] + [f"- **{k}:** `{v}`" for k, v in lineage.items()]
    if tinfo.get("caveats"):
        lines += ["", "## Giới hạn cần nhớ", ""] + [f"- {c}" for c in tinfo["caveats"]]
    if extra:
        lines += ["", *extra]
    path = folder / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def register(catalog: Path, kind: str, task: str, run_id: str, files: list[Path], produced_by: str,
             root: Path, rows: dict[str, int] | None = None) -> None:
    """Thêm (append) một dòng vào data/CATALOG.csv cho mỗi file artifact."""
    new = not catalog.exists()
    catalog.parent.mkdir(parents=True, exist_ok=True)
    with open(catalog, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CATALOG_FIELDS)
        if new:
            w.writeheader()
        for p in files:
            w.writerow({"created_at_utc": datetime.now(UTC).isoformat(timespec="seconds"), "kind": kind,
                        "task": task, "run_id": run_id, "path": p.relative_to(root).as_posix(),
                        "rows": (rows or {}).get(p.name, ""), "bytes": p.stat().st_size,
                        "sha256": sha256_file(p), "produced_by": produced_by})
    render_catalog(catalog, root / "README.md")


START, END = "<!-- CATALOG:START -->", "<!-- CATALOG:END -->"
_KIND = {"features": "(1) đã xử lý", "models": "(3) mô hình", "predictions": "(2) dự đoán",
         "synthetic": "⚠️ GIẢ ĐỊNH"}


def render_catalog(catalog: Path, readme: Path) -> None:
    """Viết lại phần giữa START/END trong data/README.md từ CATALOG.csv (mỗi path giữ dòng mới nhất)."""
    with open(catalog, encoding="utf-8", newline="") as f:
        latest = {r["path"]: r for r in csv.DictReader(f)}
    rows = sorted(latest.values(), key=lambda r: (r["task"], r["run_id"], r["kind"], r["path"]), reverse=True)
    lines = [START, "", "_Tự sinh bởi `sky-ml` từ `CATALOG.csv` — không sửa tay phần này._", "",
             "| Task | Run mới nhất | Dự đoán mới nhất |", "|---|---|---|"]
    for task in sorted({r["task"] for r in rows if r["kind"] != "synthetic"}):
        runs = sorted({r["run_id"] for r in rows if r["task"] == task})
        preds = sorted(r["path"] for r in rows if r["task"] == task and r["kind"] == "predictions"
                       and r["path"].endswith(".csv"))
        lines.append(f"| `{task}` | `{runs[-1]}` | {f'[`{preds[-1]}`]({preds[-1]})' if preds else '—'} |")
    if any(r["kind"] == "synthetic" for r in rows):
        lines.append("| ⚠️ dữ liệu giả định | `1_synthetic` | [`1_synthetic/README.md`](1_synthetic/README.md) |")
    lines += ["", "| Nhóm | Task | Run | File | Số hàng | Byte | SHA-256 (12 ký tự đầu) | Lệnh tạo |",
              "|---|---|---|---|---|---|---|---|"]
    lines += [f"| {_KIND.get(r['kind'], r['kind'])} | `{r['task']}` | `{r['run_id']}` | [`{r['path']}`]({r['path']}) "
              f"| {r['rows']} | {r['bytes']} | `{r['sha256'][:12]}` | `{r['produced_by']}` |" for r in rows]
    lines += ["", END]
    block = "\n".join(lines)
    text = readme.read_text(encoding="utf-8") if readme.exists() else f"# data/\n\n## Danh mục dữ liệu\n\n{START}\n{END}\n"
    if START in text and END in text:
        text = text[:text.index(START)] + block + text[text.index(END) + len(END):]
    else:
        text = text.rstrip() + "\n\n## Danh mục dữ liệu\n\n" + block + "\n"
    readme.write_text(text, encoding="utf-8")
