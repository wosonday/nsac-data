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
    import matplotlib.pyplot as plt

    ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()
    return ROOT, Path, glob, json, mo, pd, plt


@app.cell
def _(mo):
    mo.md(
        """
        # 05 · File dự đoán — `data/4_predictions/<task>/<run>/`

        Hai loại nội dung:

        1. **`external_backtest.csv`** — backtest trên 6 persona (ngoài cohort train Campaign 3):
           cột `subject_id, cutoff_time, model, unit, prediction, low90, high90, abstain, reasons, in_sample, y_true, abs_error`.
        2. **Dự đoán mới nhất (`*_latest_*.csv`/`.json`)** — chạy bằng `deploy_model`; với input giả định,
           tên file chứa `SYNTHETIC-INPUT` ⚠️ và `*.json` ghi `input_synthetic: true`.
        """
    )
    return


@app.cell
def _(ROOT, glob, mo, pd):
    rows = []
    for _p in sorted(glob.glob(str(ROOT / "data" / "4_predictions" / "*" / "*"))):
        _task = _p.split("/")[-2]
        run = _p.split("/")[-1]
        for f in Path(_p).iterdir():
            if f.suffix in (".csv", ".json") and f.name != "README.md":
                rows.append({"task": _task, "run": run, "file": f.name, "KB": round(f.stat().st_size / 1e3, 1)})
    inv = pd.DataFrame(rows)
    mo.vstack(
        [mo.md(f"## Kiểm kê file dự đoán — {len(inv)} file"), mo.ui.table(inv, selection=None, page_size=60)]
    )
    return


@app.cell
def _(ROOT, glob, mo):
    bt = sorted(glob.glob(str(ROOT / "data" / "4_predictions" / "*" / "2026-11-15*" / "external_backtest.csv")))
    bt = bt or sorted(glob.glob(str(ROOT / "data" / "4_predictions" / "*" / "*" / "external_backtest.csv")))
    options = {p.split("/")[-3]: p for p in bt}
    backtest = mo.ui.dropdown(options=options, value=list(options)[0] if options else None, label="Chọn task (external backtest)")
    backtest
    return (backtest,)


@app.cell
def _(backtest, mo, pd):
    df = pd.read_csv(backtest.value)
    df["cutoff_time"] = pd.to_datetime(df["cutoff_time"])
    mo.md(
        f"""
        ## `{backtest.value.split('/')[-3]}` — external backtest ({len(df)} dòng)

        in_sample: `{sorted(df['in_sample'].unique())}` · model: `{sorted(df['model'].unique())}` ·
        abstain: `{int(df['abstain'].sum())}` dòng
        """
    )
    return (df,)


@app.cell
def _(df, mo):
    per = df.groupby("subject_id").agg(rows=("y_true", "size"), mae=("abs_error", "mean")).round(3).reset_index()
    mo.vstack([mo.md("## MAE theo persona (ngoài cohort)"), mo.ui.table(per, selection=None)])
    return


@app.cell
def _(df, plt):
    subjects = sorted(df["subject_id"].unique())
    _fig, _axes = plt.subplots(len(subjects), 1, figsize=(10, 2.2 * len(subjects)), sharex=False)
    if len(subjects) == 1:
        _axes = [_axes]
    for ax, s in zip(_axes, subjects):
        sub = df[df["subject_id"] == s].sort_values("cutoff_time")
        ax.plot(sub["cutoff_time"], sub["y_true"], "k-", label="y_true", linewidth=1.5)
        ax.plot(sub["cutoff_time"], sub["prediction"], "--", label="prediction", color="#c0392b", linewidth=1.5)
        if sub["low90"].notna().any():
            ax.fill_between(sub["cutoff_time"], sub["low90"], sub["high90"], alpha=0.15, color="#c0392b")
        ax.set_title(s, fontsize=9)
        ax.tick_params(labelsize=7)
    _axes[0].legend(loc="upper right", fontsize=8)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(ROOT, glob, json, mo, pd):
    latest = sorted(glob.glob(str(ROOT / "data" / "4_predictions" / "*" / "2026-11-15*" / "*_latest_*.csv")))
    latest_rows = []
    for _p in latest:
        df2 = pd.read_csv(_p)
        _task = _p.split("/")[-3]
        latest_rows.append({
            "task": _task,
            "file": Path(_p).name,
            "synthetic_input": "SYNTHETIC-INPUT" in _p,
            "rows": len(df2),
            "cols": ", ".join(df2.columns[:8]),
        })
    mo.vstack(
        [
            mo.md("## Dự đoán mới nhất (run 2026-11-15*, bản đang kích hoạt)"),
            mo.ui.table(pd.DataFrame(latest_rows), selection=None),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## Đọc kết quả sao cho đúng

        - `in_sample = True` (vd. `dose`): chuỗi đã học, giờ DỰ BÁO chưa xảy ra — hợp lệ để minh họa, không phải đánh giá.
        - `in_sample = False` + external backtest: con số đáng tin nhất cho 6 persona.
        - File có `SYNTHETIC-INPUT`: input là dữ liệu giả định, dự đoán chỉ để minh họa.
        - `abstain`/`reasons`: model từ chối trả lời khi thiếu đặc trưng hoặc ngoài miền huấn luyện — hiển thị UNKNOWN trên web.
        """
    )
    return


if __name__ == "__main__":
    app.run()
