import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    import matplotlib.pyplot as plt

    ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()
    return ROOT, mo, pd, plt


@app.cell
def _(mo):
    mo.md(
        """
        # 01 · Danh mục artifact — `data/CATALOG.csv`

        Mỗi file pipeline sinh ra đều được đăng ký trong `CATALOG.csv` (đường dẫn, rows, bytes, sha256, ai tạo).
        Notebook này trả lời: artifact nào lớn nhất, loại nào nhiều nhất, và run mới nhất của mỗi task là gì.
        """
    )
    return


@app.cell
def _(ROOT, pd):
    cat = pd.read_csv(ROOT / "data" / "CATALOG.csv", parse_dates=["created_at_utc"])
    cat["MB"] = cat["bytes"] / 1e6
    cat["date"] = cat["created_at_utc"].dt.date
    return (cat,)


@app.cell
def _(cat, mo):
    mo.vstack(
        [
            mo.md(f"## Tổng quan — {len(cat)} entries, {cat['bytes'].sum() / 1e6:.1f} MB"),
            mo.ui.table(
                cat.groupby("kind")
                .agg(entries=("path", "count"), MB=("MB", "sum"), rows=("rows", "sum"))
                .round(1)
                .reset_index(),
                selection=None,
            ),
        ]
    )
    return


@app.cell
def _(cat, plt):
    _by_task = cat.groupby("task")["MB"].sum().sort_values()
    _fig, _ax = plt.subplots(figsize=(9, 7))
    _ax.barh(_by_task.index, _by_task.values, color="#3b6ea5")
    _ax.set_xlabel("MB (tổng mọi run)")
    _ax.set_title("Dung lượng theo task trong CATALOG.csv")
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(cat, plt):
    _by_date = cat.groupby("date")["MB"].sum().sort_index()
    _fig, _ax = plt.subplots(figsize=(10, 4))
    _ax.plot(range(len(_by_date)), _by_date.values, marker="o")
    _ax.set_xticks(range(len(_by_date)))
    _ax.set_xticklabels([str(d) for d in _by_date.index], rotation=45, ha="right")
    _ax.set_ylabel("MB/ngày")
    _ax.set_title("Dung lượng artifact sinh ra theo ngày")
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(cat, mo):
    latest = (
        cat.sort_values("created_at_utc")
        .groupby(["task", "kind"], as_index=False)
        .last()[["task", "kind", "run_id", "rows", "bytes", "produced_by"]]
    )
    latest["MB"] = (latest["bytes"] / 1e6).round(2)
    mo.vstack(
        [
            mo.md("## Run mới nhất của mỗi (task, kind)"),
            mo.ui.table(latest.sort_values(["task", "kind"]).reset_index(drop=True), selection=None, page_size=40),
        ]
    )
    return


@app.cell
def _(cat, mo):
    biggest = cat.nlargest(12, "bytes")[["task", "kind", "run_id", "path", "rows", "MB"]].copy()
    biggest["MB"] = biggest["MB"].round(2)
    mo.vstack(
        [mo.md("## 12 file lớn nhất"), mo.ui.table(biggest.reset_index(drop=True), selection=None)]
    )
    return


if __name__ == "__main__":
    app.run()
