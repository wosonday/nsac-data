"""README.md (data card) cho 3 nhóm dữ liệu, dựng HOÀN TOÀN từ file đã có trên đĩa.

Dùng chung cho các bước 2–5 và cho `sky-ml refresh-docs` (viết lại README của run mới nhất mà không chạy lại mô hình).
"""
import json
from pathlib import Path

import pandas as pd

from ._datacards import write_card
from ._settings import load_dictionary

SYNTHETIC_BANNER = ["## ⚠️ DỮ LIỆU GIẢ ĐỊNH", "",
                    ("Thư mục này có dự đoán chạy trên **dữ liệu giả định** (`data/1_synthetic`, tên file chứa "
                     "`_SYNTHETIC-INPUT`, cột `input_synthetic = True`). Kết quả chỉ để MINH HỌA; web phải gắn nhãn "
                     "\"Dữ liệu giả định\". Mô hình vẫn được train trên dữ liệu thật."),
                    ("Với đầu vào giả định: `subject_id` là persona analog theo `configs/crew_map.yaml`; "
                     "`cutoff_time` có thể là lịch nhân tạo (2000-01-01 + ngày nghiên cứu), không phải ngày thật.")]
SECURITY = ["## Cảnh báo bảo mật", "",
            ("File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` "
             "(kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.")]


def rel(data_root: Path, path: Path) -> str:
    """Đường dẫn tương đối so với data/ (README không phụ thuộc máy)."""
    try:
        return "data/" + Path(path).resolve().relative_to(data_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def features_card(settings, task: str, cfg: dict, rp) -> Path:
    out, root = rp.features, settings.features_dir.parent
    table = pd.read_csv(out / "table.csv.gz")
    features = _json(out / "features.json") or []
    files = {"table.csv.gz": "Bảng mẫu TRAIN: subject_id, cutoff_time, đặc trưng, target",
             "features.json": "Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml)",
             "snapshot.json": "SHA-256 file nguồn + phiên bản thư viện + seed (tái lập)"}
    facts = {"Số hàng (mẫu)": len(table), "Số người/chuỗi độc lập": table.subject_id.nunique(),
             "Số đặc trưng": len(features), "Target": f"`{cfg['target']}` ({cfg.get('unit')})",
             "Cửa sổ": cfg.get("window", "— (một hàng / người)")}
    if (out / "external.csv.gz").exists():
        ext = pd.read_csv(out / "external.csv.gz")
        files["external.csv.gz"] = ("Bảng NGOÀI cohort (cùng quy tắc, KHÔNG dùng để train) — "
                                    f"cohort {', '.join(cfg.get('external_cohorts', []))}; chấm điểm ở bước evaluate")
        facts["Ngoài cohort"] = f"{len(ext)} hàng, {ext.subject_id.nunique()} người ({', '.join(sorted(ext.subject_id.unique()))})"
    inputs = ", ".join(f"data/1_source/{p}" for p in cfg.get("inputs", []))
    return write_card(out, "features", task, rp.run_id, load_dictionary(settings), unit=cfg.get("unit"),
                      produced_by=f"sky-ml build-features {task}", columns=list(table.columns), files=files, facts=facts,
                      lineage={"Dữ liệu nguồn": inputs, "Mô hình dùng bảng này": rel(root, rp.models)})


def _metric_facts(summary: dict, cfg: dict) -> dict:
    metric = "mae" if cfg["kind"] == "regression" else "macro_f1"
    facts = {f"{metric} – {r['model']}": (f"{r[metric]:.4f} (CI95 {r['ci95_low']:.3f}–{r['ci95_high']:.3f}); "
                                          f"so baseline {r['diff_vs_baseline']:+.3f}") for r in summary["metrics"]}
    facts["Mô hình triển khai (chốt trước)"] = summary.get("deploy_model")
    if "permutation_test" in summary:
        pt = summary["permutation_test"]
        facts["Kiểm định hoán vị"] = f"{pt['model']}: p = {pt['p_value']:.4f} ({pt['n_permutations']} lần)"
    for key, label in (("interval_coverage", "Độ bao phủ khoảng 90%"), ("interval_coverage_deploy", "Độ bao phủ khoảng 90% (deploy)")):
        if key in summary:
            c = summary[key]
            facts[f"{label} – {c['model']}"] = f"{c['observed_coverage']:.4f} (nửa độ rộng {c['median_half_width']:.3f})"
    facts["Đơn vị độc lập"] = summary.get("units")
    ext = summary.get("external")
    if ext:
        for r in ext["metrics"]:
            facts[f"NGOÀI cohort – {r['model']}"] = (f"MAE {r['mae']:.3f} (CI95 {r['ci95_low']:.3f}–{r['ci95_high']:.3f}), "
                                                     f"{r['units']} người")
        facts["NGOÀI cohort – bao phủ khoảng 90% (deploy)"] = f"{ext['coverage_deploy']:.3f}"
    return facts


def models_card(settings, task: str, cfg: dict, rp) -> Path:
    out, root = rp.models, settings.features_dir.parent
    folds, manifest, summary = _json(out / "folds.json") or [], _json(out / "manifest.json"), _json(out / "summary.json")
    files = {"oof.csv.gz": "Dự đoán ngoài tập huấn luyện (OOF) của mọi mô hình — nguồn của mọi điểm đánh giá",
             "folds.json": "Danh sách fold và số mẫu train/test", "manifest.json": "SHA-256 + phiên bản + tham số",
             "<model>/final.joblib": "Mô hình fit trên toàn bộ người → chỉ dùng cho NGƯỜI MỚI"}
    optional = {"metrics.csv": "Metric theo đơn vị độc lập, CI95, so baseline",
                "summary.json": "Tóm tắt: metric, độ bao phủ khoảng 90%, kiểm định hoán vị, kết quả ngoài cohort",
                "confusion.csv": "Ma trận nhầm lẫn (hàng = nhãn thật, cột = nhãn dự đoán)",
                "external_metrics.csv": "MAE + CI95 trên người NGOÀI cohort (chưa từng thấy) cho mọi mô hình"}
    files.update({k: v for k, v in optional.items() if (out / k).exists()})
    facts = {"Số fold": len(folds), "Mô hình": ", ".join(cfg["models"]),
             "Số file mô hình": len(manifest["models"]) if manifest and "models" in manifest else "—"}
    if summary:
        facts.update(_metric_facts(summary, cfg))
    return write_card(out, "models", task, rp.run_id, load_dictionary(settings), unit=cfg.get("unit"),
                      produced_by=f"sky-ml train/evaluate {task}", files=files, facts=facts,
                      columns=["fold", "row", "subject_id", "model", "y_true", "y_pred"],
                      lineage={"Bảng đặc trưng (đầu vào)": rel(root, rp.features / "table.csv.gz"),
                               "Dự đoán từ các mô hình này": rel(root, rp.predictions)},
                      extra=SECURITY)


def predictions_card(settings, task: str, cfg: dict, rp) -> Path | None:
    out, root = rp.predictions, settings.features_dir.parent
    csvs = sorted(out.glob("*.csv"))
    if not csvs:
        return None
    files, facts, synthetic = {}, {}, False
    for p in csvs:
        meta = _json(p.with_suffix(".json"))
        if p.name == "external_backtest.csv":
            d = pd.read_csv(p)
            files[p.name] = "Dự đoán ngày tới cho người NGOÀI cohort train (chưa từng thấy), có đáp án `y_true`"
            ok = ~d.abstain
            inside = ((d.y_true >= d.low90) & (d.y_true <= d.high90))[ok]
            facts["external_backtest – người"] = f"{d.subject_id.nunique()} ({', '.join(sorted(d.subject_id.unique()))})"
            facts["external_backtest – hàng / từ chối"] = f"{len(d)} / {int(d.abstain.sum())}"
            facts["external_backtest – MAE gộp mọi hàng / bao phủ 90%"] = f"{d.abs_error[ok].mean():.3f} / {inside.mean():.3f}"
        else:
            is_syn = "_SYNTHETIC-INPUT" in p.name
            synthetic |= is_syn
            files[p.name] = ("⚠️ Dự đoán trên DỮ LIỆU GIẢ ĐỊNH" if is_syn else "Dự đoán") + " (.json cùng tên = thông tin lần chạy)"
            if meta:
                hw = meta.get("half_width_90")
                facts[p.stem] = (f"mô hình {meta['model']}, chế độ {meta['mode']}, {meta['n_rows']} hàng, "
                                 f"từ chối {meta['n_abstain']}, in_sample {meta['n_in_sample']}, "
                                 f"đầu vào giả định {meta.get('n_input_synthetic', 0)}"
                                 + (f", nửa độ rộng 90% {hw:.3f} {cfg.get('unit') or ''}" if hw else ""))
    latest = max(csvs, key=lambda p: p.stat().st_mtime)
    deploy = cfg.get("deploy_model") or cfg["baseline"]
    return write_card(out, "predictions", task, rp.run_id, load_dictionary(settings), unit=cfg.get("unit"),
                      produced_by=f"sky-ml predict / evaluate {task}", files=files, facts=facts,
                      columns=list(pd.read_csv(latest, nrows=0).columns),
                      lineage={"Mô hình": rel(root, rp.models / deploy / "final.joblib"),
                               "Bảng đặc trưng của run": rel(root, rp.features / "table.csv.gz")},
                      extra=SYNTHETIC_BANNER if synthetic else None)
