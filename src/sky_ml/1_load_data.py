"""Bước 1 – load_data: lấy dữ liệu từ NASA-cl về data/ và bảo đảm dữ liệu đúng.

- copy_data  : copy đúng các file các task cần, kiểm SHA-256, ghi data/COPY_MANIFEST.csv
- verify_copy: kiểm bản copy còn khớp manifest (phát hiện file bị thiếu / bị sửa)
- snapshot   : hash đầu vào + phiên bản thư viện, ghi vào mỗi run để tái lập
"""
import fnmatch
import hashlib
import json
import os
import platform
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import pandas as pd

from ._hashing import MANIFEST_NAME, sha256_file
from ._jsonio import read_json
from ._settings import Settings, ensure_writable

# Đường dẫn/glob tương đối trong NASA-cl/data
ALLOWLIST = [
    "raw/nlsp/MR080G.zip", "raw/nlsp/MR079G.zip", "raw/nlsp/BRSMImmune.zip",   # cpet
    "raw/nlsp/download_manifest.csv",
    "raw/nlsp/BRSMAct.zip",                                                      # sleep_act
    "raw/nlsp/CRF.zip",                                                          # vitals
    "raw/nlsp/NNX10AP86G.zip",                                                   # mood, glucose
    "raw/sleep_edfx/1.0.0/sleep-cassette/SC40?1*-PSG.edf",                       # sleep
    "raw/sleep_edfx/1.0.0/sleep-cassette/SC40?1*-Hypnogram.edf",
    "raw/sleep_edfx/1.0.0/download_manifest.csv",
    "raw/sleep_edfx/1.0.0/LICENSE.html", "raw/sleep_edfx/1.0.0/SHA256SUMS.txt",
    "processed/sample-v2/mmash_minutes.csv.gz",                                  # hr
    "processed/sample-v2/manifest.json", "processed/sample-v2/quality_report.md",
    "raw/mmash/1.0.0/LICENSE.txt",
    "raw/radlab/instruments/Lidal/*.csv", "raw/radlab/instruments/Lidal/*.csv.meta.json",  # dose
]


@dataclass(frozen=True)
class CopyItem:
    rel_path: str
    expected_sha256: str | None
    hash_source: str  # "nasa_cl_manifest" | "computed"


def _known_hashes(src: Path) -> dict[str, str]:
    """Hash do chính NASA-cl công bố: manifest Sleep-EDF, manifest sample-v2, sidecar RadLab."""
    known = {}
    sleep = src / "raw/sleep_edfx/1.0.0/download_manifest.csv"
    if sleep.exists():
        for row in pd.read_csv(sleep).itertuples():
            known[f"raw/sleep_edfx/1.0.0/{row.file_name}"] = row.local_sha256
    sample = src / "processed/sample-v2/manifest.json"
    if sample.exists():
        for name, meta in json.loads(sample.read_text(encoding="utf-8"))["outputs"].items():
            known[f"processed/sample-v2/{name}"] = meta["sha256"]
    for meta in (src / "raw/radlab/instruments/Lidal").glob("*.csv.meta.json"):
        known[meta.relative_to(src).as_posix().removesuffix(".meta.json")] = read_json(meta)["sha256"]
    return known


def build_allowlist(src: Path) -> list[CopyItem]:
    known, items = _known_hashes(src), []
    for pattern in ALLOWLIST:
        matches = sorted(src.glob(pattern))
        if not matches:
            raise FileNotFoundError(f"Thiếu trong NASA-cl: {pattern}")
        for path in matches:
            rel = path.relative_to(src).as_posix()
            sha = known.get(rel)
            items.append(CopyItem(rel, sha, "nasa_cl_manifest" if sha else "computed"))
    return items


def _copy_one(src: Path, dst: Path) -> str:
    """Copy qua file .part rồi đổi tên: không bao giờ để file dở dang ở đích."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    part, h = dst.with_name(dst.name + ".part"), hashlib.sha256()
    try:
        with open(src, "rb") as fin, open(part, "wb") as fout:
            for chunk in iter(lambda: fin.read(1 << 20), b""):
                h.update(chunk)
                fout.write(chunk)
        os.replace(part, dst)
    finally:
        part.unlink(missing_ok=True)
    return h.hexdigest()




def copy_data(settings: Settings, dry_run: bool = False) -> pd.DataFrame:
    src, dst_root = settings.nasa_cl_data, ensure_writable(settings.data_dir, settings)
    items = build_allowlist(src)
    if dry_run:
        size = sum((src / i.rel_path).stat().st_size for i in items)
        print(f"Sẽ copy {len(items)} file, {size / 2**20:.1f} MB từ {src}")
        return pd.DataFrame([i.__dict__ for i in items])

    old = {}
    if (dst_root / MANIFEST_NAME).exists():
        old = pd.read_csv(dst_root / MANIFEST_NAME).set_index("rel_path").sha256.to_dict()
    rows = []
    for item in items:
        source, target = src / item.rel_path, dst_root / item.rel_path
        expected = item.expected_sha256 or old.get(item.rel_path)
        if target.exists() and expected and sha256_file(target) == expected:
            sha, status = expected, "skipped_ok"
        else:
            sha, status = _copy_one(source, target), "copied"
            if item.expected_sha256 and sha != item.expected_sha256:
                target.unlink()
                raise ValueError(f"sha256 lệch manifest NASA-cl: {item.rel_path}")
        rows.append({"rel_path": item.rel_path, "bytes": target.stat().st_size, "sha256": sha,
                     "hash_source": item.hash_source, "status": status,
                     "copied_at_utc": datetime.now(UTC).isoformat(timespec="seconds")})
    table = pd.DataFrame(rows)
    table.to_csv(dst_root / MANIFEST_NAME, index=False)
    return table


# ------------------------------------------------------------------ kiểm tra bản copy
LIBRARIES = ["scikit-learn", "lightgbm", "pandas", "numpy", "scipy", "mne", "shap"]


def expand_inputs(settings: Settings, patterns: list[str]) -> list[str]:
    """Mẫu glob trong `inputs` (vd. raw/sleep_edfx/**/SC4*-PSG.edf) → danh sách rel_path có trong COPY_MANIFEST."""
    manifest = pd.read_csv(settings.data_dir / MANIFEST_NAME).rel_path.tolist()
    out = []
    for pat in patterns:
        hits = sorted(r for r in manifest if fnmatch.fnmatch(r, pat)) if any(ch in pat for ch in "*?[") else [pat]
        if not hits:
            raise ValueError(f"Mẫu inputs không khớp file nào trong COPY_MANIFEST: {pat}")
        out += hits
    return out


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
