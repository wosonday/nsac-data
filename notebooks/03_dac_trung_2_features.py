import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    import matplotlib.pyplot as plt
    import yaml

    ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()
    return ROOT, mo, pd, plt, yaml


@app.cell
def _(mo):
    mo.md(
        """
        # 03 · Bảng đặc trưng — `data/2_features/<task>/<run>/table.csv.gz`

        Mỗi task có một hoặc nhiều run; notebook dùng **run mới nhất** (theo tên thư mục `YYYY-MM-DD_HHMMSS`).
        Schema khác nhau theo builder (`hr|dose|cpet|sleep|vitals|mood|prepost|…`) — notebook tự thích ứng:

        - `target` lấy từ `configs/tasks.yaml` (fallback: cột cuối);
        - cột `subject_id` luôn có (trừ một số bảng mô tả).
        """
    )
    return


@app.cell
def _(ROOT, mo):
    feats = sorted(d.name for d in (ROOT / "data" / "2_features").iterdir() if d.is_dir())
    task = mo.ui.dropdown(options=feats, value=feats[0], label="Chọn task")
    task
    return (task,)


@app.cell
def _(ROOT, mo, pd, task, yaml):
    tasks_cfg = yaml.safe_load((ROOT / "configs" / "tasks.yaml").read_text()) or {}
    cfg = tasks_cfg.get(task.value, {})
    kind = cfg.get("kind", "?")
    target = cfg.get("target", cfg.get("member", None))
    run_dir = sorted((ROOT / "data" / "2_features" / task.value).iterdir())[-1]
    df = pd.read_csv(run_dir / "table.csv.gz")
    mo.md(
        f"""
        ## `{task.value}` — run `{run_dir.name}` · kind `{kind}` · target `{target}`

        **{df.shape[0]}** hàng × **{df.shape[1]}** cột · `{cfg.get('description', '')}`
        """
    )
    return df, target


@app.cell
def _(df, mo):
    mo.vstack([mo.md("## 5 hàng đầu"), mo.ui.table(df.head(), selection=None)])
    return


@app.cell
def _(df, mo):
    missing = df.isna().sum()
    missing = missing[missing > 0]
    if len(missing) == 0:
        _out = mo.md("## Thiếu dữ liệu\n\nKhông có giá trị thiếu trong bảng đặc trưng.")
    else:
        _out = mo.vstack(
            [mo.md("## Thiếu dữ liệu"), mo.ui.table(missing.rename("n_missing").to_frame(), selection=None)]
        )
    _out
    return


@app.cell
def _(df, mo):
    mo.vstack(
        [
            mo.md("## Mô tả số (numeric)"),
            mo.ui.table(df.describe().T.round(3).reset_index(names="column"), selection=None, page_size=60),
        ]
    )
    return


@app.cell
def _(df, mo, plt, target):
    tgt = target if target in df.columns else df.columns[-1]
    if df[tgt].dtype == object and df[tgt].nunique() <= 12:
        _out = mo.vstack(
            [mo.md(f"## Phân phối target `{tgt}`"), mo.ui.table(df[tgt].value_counts().rename("count").to_frame(), selection=None)]
        )
    else:
        _fig, _ax = plt.subplots(figsize=(8, 3.5))
        _ax.hist(df[tgt].dropna(), bins=40, color="#3b6ea5")
        _ax.set_xlabel(tgt)
        _ax.set_title(f"Phân phối {tgt} (n={df[tgt].notna().sum()})")
        _fig.tight_layout()
        _out = mo.vstack([mo.md(f"## Phân phối target `{tgt}`"), _fig])
    _out
    return


@app.cell
def _(df, mo, target):
    tgt2 = target if target in df.columns else df.columns[-1]
    numeric = df.select_dtypes("number").columns.tolist()
    corr = df[numeric].corr(numeric_only=True)
    if tgt2 in corr.columns and len(corr) > 1:
        s = corr[tgt2].drop(labels=[tgt2], errors="ignore").abs().sort_values(ascending=False)
        _out = mo.vstack(
            [mo.md(f"## Tương quan |r| với `{tgt2}` (top 15)"), mo.ui.table(s.head(15).round(3).rename("|r|").to_frame(), selection=None)]
        )
    else:
        _out = mo.md("## Tương quan\n\nBỏ qua (target không phải numeric liên tục hoặc chỉ có 1 cột).")
    _out
    return


@app.cell
def _(df, mo):
    if "subject_id" not in df.columns:
        _out = mo.md("## Theo subject\n\nBảng không có `subject_id`, bỏ qua.")
    else:
        per = df.groupby("subject_id").size().rename("rows").reset_index().sort_values("rows", ascending=False)
        _out = mo.vstack(
            [mo.md(f"## Số hàng theo subject ({per['subject_id'].nunique()} subject)"), mo.ui.table(per, selection=None, page_size=40)]
        )
    _out
    return


if __name__ == "__main__":
    app.run()
