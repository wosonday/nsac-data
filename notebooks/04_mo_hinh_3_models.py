import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import json
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()
    return ROOT, json, mo, np, pd, plt


@app.cell
def _(mo):
    mo.md(
        """
        # 04 · Kết quả mô hình — `data/3_models/<task>/<run>/`

        Mỗi run gồm `summary.json` (metrics + CI95 + coverage), `metrics.csv`, `oof.csv.gz`
        (dự đoán **out-of-fold** = held-out, không in-sample) và mô hình đã serialize.

        - CI95 lấy mẫu lại **theo đơn vị độc lập** (subject / tháng / người), không theo hàng.
        - `deploy_model` được chọn **trước**, không theo điểm test.
        - Task mô tả (`dxa_regional`, `cortisol`, `inspiration4_labs`) không có thư mục mô hình.
        - `muscle_quadriceps`: **không mô hình nào tốt hơn baseline** — giữ persistence.
        """
    )
    return


@app.cell
def _(ROOT, mo):
    modelled = sorted(d.name for d in (ROOT / "data" / "3_models").iterdir() if d.is_dir())
    task = mo.ui.dropdown(options=modelled, value=modelled[0] if modelled else None, label="Chọn task")
    task
    return (task,)


@app.cell
def _(ROOT, json, mo, pd, task):
    run_dir = sorted((ROOT / "data" / "3_models" / task.value).iterdir())[-1]
    summary = json.loads((run_dir / "summary.json").read_text())
    metrics = pd.read_csv(run_dir / "metrics.csv")
    ext_path = run_dir / "external_metrics.csv"
    external = pd.read_csv(ext_path) if ext_path.exists() else None
    deploy = summary["deploy_model"]
    is_clf = "macro_f1" in metrics.columns
    metric_col = "macro_f1" if is_clf else "mae"
    mo.md(
        f"""
        ## `{task.value}` — run `{run_dir.name}`

        deploy_model: **`{deploy}`** · samples: **{summary.get('samples')}** · units: **{summary.get('units')}** ·
        metric hiển thị: **{metric_col}** {'(phân loại)' if is_clf else '(hồi quy, thấp = tốt)'}
        """
    )
    return deploy, external, is_clf, metric_col, metrics, run_dir, summary


@app.cell
def _(metrics, mo):
    mo.vstack(
        [mo.md("## Bảng metrics (CI95 theo đơn vị độc lập)"), mo.ui.table(metrics.round(4), selection=None)]
    )
    return


@app.cell
def _(deploy, metrics, metric_col, np, plt):
    _m = metrics.sort_values(metric_col)
    _yerr = np.vstack([_m[metric_col] - _m["ci95_low"], _m["ci95_high"] - _m[metric_col]])
    _colors = ["#c0392b" if x == deploy else "#3b6ea5" for x in _m["model"]]
    _fig, _ax = plt.subplots(figsize=(8, 4))
    _ax.bar(_m["model"], _m[metric_col], yerr=_yerr, capsize=4, color=_colors)
    _ax.set_ylabel(metric_col)
    _ax.set_title(f"{metric_col} ± CI95 (đỏ = deploy_model)")
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(deploy, is_clf, mo, np, run_dir):
    oof = pd.read_csv(run_dir / "oof.csv.gz")
    sub = oof[oof["model"] == deploy]
    if is_clf:
        counts = sub.groupby("y_true").size().rename("n").reset_index()
        _out = mo.vstack(
            [
                mo.md(
                    f"""
                    ## OOF — `{deploy}` (phân loại)

                    {len(sub)} epoch dự đoán. Với bài toán 5 lớp ngủ/ epoch 30 s, xem bảng `metrics.csv`
                    (macro-F1, balanced accuracy, cohen kappa, brier) — scatter y_true/y_pred không có ý nghĩa.
                    """
                ),
                mo.ui.table(counts, selection=None),
            ]
        )
    elif len(sub):
        _fig, _axes = plt.subplots(1, 2, figsize=(11, 4))
        if len(sub) > 4000:
            sub = sub.sample(4000, random_state=17)
        _axes[0].scatter(sub["y_true"], sub["y_pred"], s=8, alpha=0.4, color="#3b6ea5")
        lim = [min(sub["y_true"].min(), sub["y_pred"].min()), max(sub["y_true"].max(), sub["y_pred"].max())]
        _axes[0].plot(lim, lim, "k--", alpha=0.6)
        _axes[0].set_xlabel("y_true")
        _axes[0].set_ylabel("y_pred")
        _axes[0].set_title(f"OOF scatter — {deploy}")
        resid = sub["y_pred"] - sub["y_true"]
        _axes[1].hist(resid, bins=40, color="#3b6ea5")
        _axes[1].axvline(0, color="k", linestyle="--", alpha=0.6)
        _axes[1].set_xlabel("y_pred − y_true")
        _axes[1].set_title(f"Phân phối residual (bias {resid.mean():+.3f})")
        _fig.tight_layout()
        _out = mo.vstack([mo.md(f"## OOF — `{deploy}`"), _fig])
    else:
        _out = mo.md(f"## OOF — không có hàng nào cho model `{deploy}`")
    _out
    return


@app.cell
def _(mo, summary):
    cov = summary.get("interval_coverage")
    if isinstance(cov, dict):
        _out = mo.md(
            f"""
            ## Khoảng dự đoán 90% — `{cov.get('model')}`

            - Mục tiêu bao phủ: **{cov.get('target_coverage')}** · quan sát: **{cov.get('observed_coverage'):.3f}**
            - Nửa rộng trung bình: **{cov.get('median_half_width'):.3f}**
            """
        )
    else:
        _out = mo.md("## Khoảng dự đoán 90% — không có (task không dùng interval hoặc là phân loại)")
    _out
    return


@app.cell
def _(external, mo):
    if external is not None:
        _out = mo.vstack(
            [
                mo.md("## Test NGOÀI cohort (6 persona, in_sample = False)"),
                mo.ui.table(external.round(4), selection=None),
            ]
        )
    else:
        _out = mo.md("## Test ngoài cohort — không có (cohort không có nhánh external)")
    _out
    return


if __name__ == "__main__":
    app.run()
