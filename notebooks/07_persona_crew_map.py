import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    import yaml

    ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()
    return ROOT, mo, pd, yaml


@app.cell
def _(mo):
    mo.md(
        """
        # 07 · Persona hư cấu → analog thật — `configs/crew_map.yaml`

        Sáu phi hành gia **hư cấu** của nsac, mỗi người map tới **đúng một** người analog đã khử danh
        (UTMB bed rest CFT70 / Campaign 1). Không trộn người, không trộn cohort. Chỉ để minh họa —
        không suy ra danh tính.
        """
    )
    return


@app.cell
def _(ROOT, yaml):
    crew = yaml.safe_load((ROOT / "configs" / "crew_map.yaml").read_text())
    return (crew,)


@app.cell
def _(crew, mo, pd):
    personas = pd.DataFrame([{"persona": p, **v} for p, v in crew["personas"].items()])
    mo.vstack([mo.md("## 6 persona"), mo.ui.table(personas, selection=None)])
    return


@app.cell
def _(crew, mo, pd):
    indicators = crew["indicators"]
    matrix = pd.DataFrame(
        [{"indicator": ind, "CFT70": v.get("cft70", "—"), "Campaign 1": v.get("campaign_1", "—")} for ind, v in indicators.items()]
    )
    matrix["loại (CFT70)"] = matrix["CFT70"].str.split(":").str[0]
    matrix["loại (C1)"] = matrix["Campaign 1"].str.split(":").str[0]
    mo.vstack(
        [
            mo.md("## Chỉ số web theo cohort — nguồn thật / giả định / không có"),
            mo.ui.table(matrix, selection=None, page_size=40),
        ]
    )
    return (matrix,)


@app.cell
def _(matrix, mo):
    def classify(s: str) -> str:
        s = s.lower()
        if s.startswith("real"):
            return "real"
        if s.startswith("synthetic"):
            return "synthetic"
        if s.startswith("none"):
            return "none"
        return "mixed/other"

    counts = {
        "CFT70": matrix["loại (CFT70)"].map(classify).value_counts().to_dict(),
        "Campaign 1": matrix["loại (C1)"].map(classify).value_counts().to_dict(),
    }
    mo.md(
        f"""
        ## Thống kê độ phủ

        - **CFT70** (persona: ayla-reyes, dae-jung-park, lena-fischer): `{counts['CFT70']}`
        - **Campaign 1** (persona: tomas-ortega, yuki-tanaka, noor-abbasi): `{counts['Campaign 1']}`

        `real` = dữ liệu đo thật của analog · `synthetic` = DỮ LIỆU GIẢ ĐỊNH (notebook 06) ·
        `none` = không có (web hiển thị UNKNOWN) · `mixed/other` = kết hợp thật + giả định hoặc ghi chú riêng.
        """
    )
    return


@app.cell
def _(crew, mo, pd):
    rows = [
        {"persona": persona, "analog": spec["analog"], "cohort": spec["cohort"], "bed_rest_days": spec["bed_rest_days"]}
        for persona, spec in crew["personas"].items()
    ]
    mo.vstack(
        [
            mo.md(
                """
                ## Quy tắc khi hiển thị (web / báo cáo)

                - Mỗi persona chỉ dùng dữ liệu của **đúng analog của nó** — không lấy từ người khác, không trộn cohort.
                - Chỉ số `none` → hiển thị **UNKNOWN**, không bịa số.
                - Chỉ số `synthetic` → gắn nhãn **"Dữ liệu giả định"**.
                - Chỉ số `real` → có thể hiển thị như quan sát của analog (bed rest), không phải của phi hành gia.
                """
            ),
            mo.ui.table(pd.DataFrame(rows), selection=None),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
