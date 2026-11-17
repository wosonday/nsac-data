import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import json
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    import matplotlib.pyplot as plt

    ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()
    return ROOT, json, mo, pd, plt


@app.cell
def _(mo):
    mo.md(
        """
        # 06 · ⚠️ DỮ LIỆU GIẢ ĐỊNH — `data/1_synthetic/`

        > **DỮ LIỆU GIẢ ĐỊNH — KHÔNG PHẢI SỐ ĐO THẬT.**
        > Sinh bằng `sky-ml make-synthetic` (seed 17) để lấp chỗ persona không có dữ liệu thật.
        > Không dùng để train hay đánh giá mô hình. Web PHẢI gắn nhãn "Dữ liệu giả định".

        Mô hình sinh: `y_it = μ(t) + b_i + e_it`, `b_i ~ N(0, σ_b)`, `e_it` AR(1) với ρ, SD σ_e.
        Mọi tham số ước lượng từ dữ liệu THẬT và ghi ở `<tên>.params.json`; `<tên>.validation.csv`
        so sánh thống kê giữa THẬT (dùng để sinh) và GIẢ ĐỊNH.
        """
    )
    return


@app.cell
def _(ROOT, mo):
    synth = ROOT / "data" / "1_synthetic"
    files = {
        p.name: p
        for p in synth.glob("*.csv")
        if not p.name.endswith(".validation.csv") and p.name != "SYNTHETIC_MANIFEST.csv"
    }
    dd = mo.ui.dropdown(options=sorted(files), value=sorted(files)[0], label="Chọn bộ dữ liệu giả định")
    dd
    return dd, files


@app.cell
def _(ROOT, dd, files, mo, pd):
    df = pd.read_csv(files[dd.value])
    stem = dd.value[: -len(".csv")]
    params_path = ROOT / "data" / "1_synthetic" / f"{stem}.params.json"
    val_path = ROOT / "data" / "1_synthetic" / f"{stem}.validation.csv"
    params = json.loads(params_path.read_text()) if params_path.exists() else None
    validation = pd.read_csv(val_path) if val_path.exists() else None
    real_n = int((~df["is_synthetic"]).sum()) if "is_synthetic" in df else 0
    synth_n = int(df["is_synthetic"].sum()) if "is_synthetic" in df else len(df)
    persona_list = sorted(df["persona"].unique()) if "persona" in df else "—"
    mo.md(
        f"""
        ## `{dd.value}` — {len(df)} hàng · giả định **{synth_n}** / thật (neo) **{real_n}**

        Persona: `{persona_list}`
        """
    )
    return df, params, stem, validation


@app.cell
def _(df, mo):
    mo.vstack(
        [
            mo.md("## 5 hàng đầu (cột `is_synthetic`: True = sinh giả định, False = điểm neo thật)"),
            mo.ui.table(df.head(), selection=None),
        ]
    )
    return


@app.cell
def _(df, plt):
    value_cols = [c for c in df.columns if c not in ("persona", "subject_id", "study_day", "date", "is_synthetic", "generator")]
    col = value_cols[0]
    personas = sorted(df["persona"].unique()) if "persona" in df else ["(tất cả)"]
    _fig, _axes = plt.subplots(len(personas), 1, figsize=(10, 2.6 * len(personas)), sharex=True)
    if len(personas) == 1:
        _axes = [_axes]
    for ax, p in zip(_axes, personas):
        sub = df[df["persona"] == p].sort_values("study_day") if "persona" in df else df.sort_values("study_day")
        ax.plot(sub["study_day"], sub[col], "-o", markersize=3, label="giả định", color="#3b6ea5")
        if "is_synthetic" in sub:
            anchor = sub[~sub["is_synthetic"]]
            if len(anchor):
                ax.scatter(anchor["study_day"], anchor[col], color="#c0392b", s=45, zorder=5, label="thật (neo)")
        ax.set_title(f"{p} — {col}", fontsize=9)
        ax.grid(alpha=0.3)
    _axes[0].legend(loc="upper right", fontsize=8)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(mo, validation):
    if validation is not None:
        _out = mo.vstack(
            [mo.md("## Hiệu chuẩn: THẬT (dùng để sinh) vs GIẢ ĐỊNH"), mo.ui.table(validation, selection=None)]
        )
    else:
        _out = mo.md("## Hiệu chuẩn\n\nKhông có `.validation.csv` cho bộ này.")
    _out
    return


@app.cell
def _(json, mo, params, stem):
    mo.md(f"## Tham số sinh — `{stem}.params.json`\n\n```json\n{json.dumps(params, indent=2, ensure_ascii=False)}\n```")
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## Giới hạn cần nhớ

        1. Giá trị sinh phản ánh phân bố **quần thể analog**, không phải người analog cụ thể (trừ điểm neo thật).
        2. Không mô phỏng sự kiện bất thường (bệnh, thuốc, sự cố) — chuỗi "bình thường" theo thống kê.
        3. `sleep_cft70_actigraphy` học từ CHỈ 3 người Campaign 1 → độ tin cậy thấp nhất.
        4. Người dùng cuối (web) chỉ được hiển thị với nhãn **"Dữ liệu giả định"**.
        """
    )
    return


if __name__ == "__main__":
    app.run()
