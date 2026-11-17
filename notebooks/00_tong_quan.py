import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import glob
    import json
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    import yaml

    ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()
    return ROOT, glob, json, mo, pd, yaml


@app.cell
def _(mo):
    mo.md(
        """
        # 00 · Tổng quan repo `nsac-data`

        Repo này chứa toàn bộ dữ liệu đã xử lý của pipeline **sky-ml** (xem `data/README.md`):

        1. **`data/1_source/`** — bản copy một lần từ repo `NASA-cl` (kiểm SHA-256), chỉ đọc.
        2. **`data/2_features/<task>/<run>/`** — bảng đặc trưng (đầu vào mô hình).
        3. **`data/3_models/<task>/<run>/`** — mô hình đã train + OOF + metrics.
        4. **`data/4_predictions/<task>/<run>/`** — dự đoán + backtest ngoài cohort.
        5. **`data/1_synthetic/`** — ⚠️ DỮ LIỆU GIẢ ĐỊNH (không train, không đánh giá).
        6. **`data/CATALOG.csv`** — sổ đăng ký mọi artifact (đường dẫn, rows, bytes, sha256, ai tạo).
        """
    )
    return


@app.cell
def _(ROOT, mo, pd, yaml):
    tasks_cfg = yaml.safe_load((ROOT / "configs" / "tasks.yaml").read_text())
    rows = []
    for name, cfg in tasks_cfg.items():
        rows.append({
            "task": name,
            "kind": cfg.get("kind", "?"),
            "target": cfg.get("target", cfg.get("member", "—")),
            "deploy_model": cfg.get("deploy_model", "—"),
            "description": cfg.get("description", ""),
        })
    tasks = pd.DataFrame(rows).sort_values(["kind", "task"]).reset_index(drop=True)
    feats = sorted(d.name for d in (ROOT / "data" / "2_features").iterdir() if d.is_dir())
    models = sorted(d.name for d in (ROOT / "data" / "3_models").iterdir() if d.is_dir())
    preds = sorted(d.name for d in (ROOT / "data" / "4_predictions").iterdir() if d.is_dir())
    mo.md(
        f"""
        ## Quy mô

        - **{len(tasks)}** task khai báo trong `configs/tasks.yaml`
        - **{len(feats)}** task có bảng đặc trưng · **{len(models)}** task có mô hình · **{len(preds)}** task có file dự đoán
        - Artifact ghi nhận trong `CATALOG.csv`: xem notebook **01_danh_muc_catalog.py**
        """
    )
    return (tasks,)


@app.cell
def _(mo, tasks):
    counts = tasks.groupby("kind").size().rename("số task").reset_index()
    mo.vstack([mo.md("## Các task theo loại"), mo.ui.table(counts, selection=None)])
    return


@app.cell
def _(mo, tasks):
    mo.vstack([mo.md("## Danh sách task"), mo.ui.table(tasks, selection=None, page_size=35)])
    return


@app.cell
def _(ROOT, mo, pd):
    cat = pd.read_csv(ROOT / "data" / "CATALOG.csv")
    summary = (
        cat.groupby("kind")
        .agg(entries=("path", "count"), bytes_total=("bytes", "sum"), rows_total=("rows", "sum"))
        .reset_index()
    )
    summary["MB"] = (summary["bytes_total"] / 1e6).round(1)
    mo.vstack(
        [mo.md("## Artifact trong `CATALOG.csv` theo kind"), mo.ui.table(summary, selection=None)]
    )
    return


@app.cell
def _(ROOT, mo):
    sizes = []
    for sub in ["1_source", "1_synthetic", "2_features", "3_models", "4_predictions"]:
        d = ROOT / "data" / sub
        if d.exists():
            total = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            sizes.append((sub, total / 1e6))
    sizes.sort(key=lambda x: -x[1])
    lines = "\n".join(f"- `data/{name}/` — {mb:.1f} MB" for name, mb in sizes)
    mo.md(f"## Dung lượng trên đĩa\n\n{lines}")
    return


if __name__ == "__main__":
    app.run()
