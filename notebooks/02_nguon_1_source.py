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
        # 02 · Nguồn gốc — `data/1_source/`

        `data/1_source/` là bản **copy một lần, hash-verified** từ sibling repo `NASA-cl` (xem `sky_ml.yaml: nasa_cl_data`).
        Mọi bước sau chỉ đọc bản copy này, không bao giờ ghi ngược vào NASA-cl.

        `COPY_MANIFEST.csv` ghi: `rel_path, bytes, sha256, hash_source, status, copied_at_utc`.
        """
    )
    return


@app.cell
def _(ROOT, pd):
    man = pd.read_csv(ROOT / "data" / "1_source" / "COPY_MANIFEST.csv")
    man["MB"] = man["bytes"] / 1e6
    man["group"] = man["rel_path"].str.split("/").str[0] + "/" + man["rel_path"].str.split("/").str[1].fillna("—")
    return (man,)


@app.cell
def _(man, mo):
    mo.md(
        f"""
        ## Tổng quan bản copy

        - **{len(man)}** file, tổng **{man['bytes'].sum() / 1e6:.1f} MB**
        - Hash: `{man['hash_source'].value_counts().to_dict()}`
        - Trạng thái: `{man['status'].value_counts().to_dict()}` (copied/skipped_ok = SHA-256 khớp manifest NASA-cl)

        ⚠️ Bản copy trong git **chỉ giữ phần mô hình đang dùng** (xem `.gitignore` và `data/README.md`).
        Đầy đủ dữ liệu gốc nằm ở NASA-cl (`D:\\Project\\NASA-cl\\data` trên máy của tác giả).
        """
    )
    return


@app.cell
def _(man, plt):
    _by = man.groupby("group")["MB"].sum().sort_values()
    _fig, _ax = plt.subplots(figsize=(9, max(3, 0.35 * len(_by))))
    _ax.barh(_by.index, _by.values, color="#3b6ea5")
    _ax.set_xlabel("MB")
    _ax.set_title("Dung lượng theo nhóm nguồn (raw/…, processed/…)")
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(man, mo):
    show = man.sort_values("bytes", ascending=False)[["rel_path", "MB", "status", "hash_source"]].copy()
    show["MB"] = show["MB"].round(2)
    mo.vstack(
        [
            mo.md("## Chi tiết từng file (sắp theo dung lượng)"),
            mo.ui.table(show.reset_index(drop=True), selection=None, page_size=54),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## Các nguồn dữ liệu chính (tóm tắt)

        | Nguồn | Nội dung | Dùng cho task |
        |---|---|---|
        | MMASH (`processed/sample-v2/mmash_minutes.csv.gz`) | HR 5 phút/người (22 người, mặt đất) | `hr` |
        | RadLab Lidal (`raw/radlab/instruments/Lidal/`) | Liều bức xạ ISS/Columbus 2022 | `dose`, `dose_orbit` |
        | Sleep-EDF / UTMB (`raw/sleep_edfx/…`) | EEG epoch 30 s, 5 lớp ngủ | `sleep` |
        | BRSMAct Campaign 1 | Actigraphy 3 người | `sleep_act`, `sleep_act_duration` |
        | UTMB CFT70 + Campaign 1/3 (`raw/nlsp/*.zip` CRF, OGTT, POMS, iDXA, MRI, echo tim, nhịp/huyết áp/nhiệt độ…) | Bed rest 60–70 ngày | `vitals_*`, `mood`, `fatigue`, `glucose`, `prepost` (lv_mass, bone_mineral, lean_mass_legs), `muscle_*`, `lipid_ldl` |
        | WinSCAT (Campaign 1/3) | Cognition CPT/MATH | `cognition_*` |
        | Inspiration4 | OSD-569/575 (labs) — mô tả, không train | `inspiration4_labs` |
        | Cortisol (Campaign 3) | Mô tả, không train | `cortisol` |

        Chi tiết cột & nguồn từng task: `docs/Tong_hop_du_lieu_mo_hinh.xlsx` và `configs/tasks.yaml`.
        """
    )
    return


if __name__ == "__main__":
    app.run()
