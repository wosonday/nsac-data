"""Hỗ trợ (ngoài luồng): dòng lệnh `sky-ml`. Mỗi lệnh con ứng với một bước đánh số trong _steps.STEPS.

Dữ liệu ghi theo 3 nhóm (xem data/README.md):
data/2_features/<task>/<run>/ (1) đầu vào mô hình · data/3_models/... (3) mô hình · data/4_predictions/... (2) dự đoán.
Mỗi thư mục có README.md tự sinh; mọi file được ghi vào data/CATALOG.csv.
"""
import argparse
import math
from datetime import datetime
from pathlib import Path

import pandas as pd

from . import _cards as cards
from ._artifacts import load_model, save_model, write_manifest
from ._datacards import register
from ._hashing import sha256_file
from ._jsonio import read_json, write_json
from ._runs import new_run, require, resolve_run
from ._settings import ensure_writable, load_settings, load_tasks
from ._steps import STEPS, build_features, evaluate, load_data, predict, train


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sky-ml")
    parser.add_argument("--config", default="sky_ml.yaml")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("steps", help="in thứ tự các bước pipeline")
    sub.add_parser("load-data", help=STEPS[1][2]).add_argument("--dry-run", action="store_true")
    sub.add_parser("check", help="(bước 1) kiểm bản copy còn khớp data/COPY_MANIFEST.csv")
    sub.add_parser("refresh-docs", help="(ngoài luồng) viết lại README của run mới nhất mọi task + danh mục data/README.md")
    sub.add_parser("make-synthetic", help="(ngoài luồng) sinh DỮ LIỆU GIẢ ĐỊNH cho persona thiếu dữ liệu → data/1_synthetic")
    sub.add_parser("build-features", help=STEPS[2][2]).add_argument("task", help="tên task trong configs/tasks.yaml")
    for name, number in (("train", 3), ("evaluate", 4)):
        p = sub.add_parser(name, help=STEPS[number][2])
        p.add_argument("task")
        p.add_argument("--run", default="latest", help="tên thư mục run hoặc 'latest'")
    p = sub.add_parser("predict", help=STEPS[5][2])
    p.add_argument("task")
    p.add_argument("--input", required=True, help="CSV dữ liệu MỚI, cùng cột với dữ liệu gốc của task")
    p.add_argument("--run", default="latest", help="run chứa mô hình đã huấn luyện (data/3_models/<task>/<run>)")
    p.add_argument("--model", default=None, help="tên mô hình; mặc định = deploy_model trong tasks.yaml")
    p.add_argument("--mode", choices=["latest", "backtest", "table"], default=None,
                   help="mặc định: latest nếu task hỗ trợ, ngược lại table")
    args = parser.parse_args(argv)

    if args.command == "steps":
        for number, (module, command, text) in STEPS.items():
            print(f"{number}. sky-ml {command:<24} {module:<17} {text}")
        return
    settings = load_settings(args.config)
    {"load-data": _load_data, "check": _check, "build-features": _build_features, "train": _train,
     "evaluate": _evaluate, "predict": _predict, "make-synthetic": _make_synthetic,
     "refresh-docs": _refresh_docs}[args.command](settings, args)


def _load_data(settings, args):
    table = load_data.copy_data(settings, dry_run=args.dry_run)
    if not args.dry_run:
        print(table.status.value_counts().to_string(), f"\n→ {settings.data_dir}")
        print(f"check: OK {load_data.verify_copy(settings)} files")


def _check(settings, args):
    print(f"OK {load_data.verify_copy(settings)} files")


def _md_table(df: pd.DataFrame) -> str:
    rows = [" | ".join(map(str, df.columns)), " | ".join("---" for _ in df.columns)]
    rows += [" | ".join("" if pd.isna(v) else str(v) for v in r) for r in df.itertuples(index=False)]
    return "\n".join(f"| {r} |" for r in rows)


def _make_synthetic(settings, args):
    """Sinh dữ liệu giả định (xem _synthetic.py) + params.json + README.md + SYNTHETIC_MANIFEST.csv + CATALOG."""
    import yaml

    from . import _synthetic
    crew_path = settings.tasks_config.parent / "crew_map.yaml"
    crew = yaml.safe_load(crew_path.read_text(encoding="utf-8"))
    nlsp = settings.data_dir / "raw/nlsp"
    load_data.verify_copy(settings, ["raw/nlsp/NNX10AP86G.zip", "raw/nlsp/BRSMAct.zip", "raw/nlsp/download_manifest.csv"])
    out = ensure_writable(settings.features_dir.parent / "1_synthetic", settings)
    out.mkdir(parents=True, exist_ok=True)
    lines = ["# data/1_synthetic — DỮ LIỆU GIẢ ĐỊNH (synthetic)", "",
             ("> ⚠️ **DỮ LIỆU GIẢ ĐỊNH — KHÔNG PHẢI SỐ ĐO THẬT.** Sinh bằng `sky-ml make-synthetic` để lấp chỗ persona "
              "không có dữ liệu thật (BTC cho phép, phải ghi rõ). Không dùng để train hay đánh giá mô hình. "
              "Web PHẢI gắn nhãn \"Dữ liệu giả định\" khi hiển thị."), "",
             f"- Bộ sinh: `{_synthetic.GEN_VERSION}` (src/sky_ml/_synthetic.py) · seed 17 · ánh xạ persona: `configs/crew_map.yaml`",
             ("- Mô hình sinh chung: `y_it = μ(t) + b_i + e_it`; `b_i ~ N(0, σ_b)`; `e_it` AR(1) với hệ số ρ, SD σ_e. "
              "Mọi tham số ước lượng từ dữ liệu THẬT trong `data/1_source` và ghi ở `<tên>.params.json`."),
             "- Cột `is_synthetic`: True = giá trị sinh ra; False = giá trị thật giữ làm điểm neo.", ""]
    files = []
    for name, (frame, params, title) in _synthetic.generate(nlsp, crew).items():
        frame.to_csv(out / f"{name}.csv", index=False)
        write_json(out / f"{name}.params.json", params)
        val = _synthetic.validation(name, frame, nlsp)
        val.to_csv(out / f"{name}.validation.csv", index=False)
        files += [out / f"{name}.csv", out / f"{name}.params.json", out / f"{name}.validation.csv"]
        lines += [f"## `{name}.csv`", "", f"**{title}**", "",
                  f"- Nguồn tham số: {params['source']}",
                  (f"- Persona: {', '.join(sorted(frame.persona.unique()))} · {len(frame)} hàng · "
                   f"giả định {int(frame.is_synthetic.sum())} / thật (neo) {int((~frame.is_synthetic).sum())}"),
                  f"- Cột: {', '.join(f'`{c}`' for c in frame.columns)}", "",
                  "Kiểm tra: thống kê giả định so với dữ liệu thật dùng để sinh", "",
                  _md_table(val.round(3)), ""]
    lines += ["## Giới hạn", "",
              "1. Giá trị sinh ra phản ánh phân bố QUẦN THỂ analog, không phản ánh người analog cụ thể (trừ điểm neo thật).",
              "2. Không mô phỏng sự kiện bất thường (bệnh, thuốc, sự cố) — chuỗi \"bình thường\" theo thống kê.",
              "3. `sleep_cft70_actigraphy` học từ CHỈ 3 người Campaign 1 → độ tin cậy thấp nhất.",
              "4. `mood_c1_poms` dùng lịch đo và xu hướng của CFT70 (70 ngày) cắt ở 60 ngày.",
              "5. Cột `date` (nếu có) là lịch nhân tạo 2000-01-01 + study_day."]
    (out / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = pd.DataFrame([{"file": f.name, "bytes": f.stat().st_size, "sha256": sha256_file(f),
                              "generator": _synthetic.GEN_VERSION, "seed": 17, "is_synthetic": True} for f in files])
    manifest.to_csv(out / "SYNTHETIC_MANIFEST.csv", index=False)
    register(_catalog(settings), "synthetic", "persona", "seed17", files + [out / "README.md"], "sky-ml make-synthetic",
             settings.features_dir.parent)
    print(f"Đã sinh {len(files) // 3} bộ dữ liệu GIẢ ĐỊNH → {out}")


def _refresh_docs(settings, args):
    """Viết lại README (data card) của run mới nhất mỗi task từ file trên đĩa — không chạy lại mô hình."""
    from ._datacards import render_catalog
    for task, cfg in load_tasks(settings).items():
        try:
            rp = resolve_run(settings, task)
        except FileNotFoundError:
            continue
        done = [cards.features_card(settings, task, cfg, rp)]
        if (rp.models / "oof.csv.gz").exists():
            done.append(cards.models_card(settings, task, cfg, rp))
        if rp.predictions.exists():
            done.append(cards.predictions_card(settings, task, cfg, rp))
        print(f"{task:<14} {rp.run_id}  {sum(d is not None for d in done)} README")
    catalog = _catalog(settings)
    if catalog.exists():
        render_catalog(catalog, settings.features_dir.parent / "README.md")


def _task_cfg(settings, task):
    tasks = load_tasks(settings)
    if task not in tasks:
        raise SystemExit(f"Task '{task}' không có trong {settings.tasks_config}; có: {', '.join(tasks)}")
    return tasks[task]


def _catalog(settings):
    return settings.features_dir.parent / "CATALOG.csv"


def _rel(settings, path) -> str:
    return cards.rel(settings.features_dir.parent, path)


def _build_features(settings, args):
    cfg = _task_cfg(settings, args.task)
    patterns = list(cfg["inputs"])
    cfg["inputs"] = load_data.expand_inputs(settings, patterns)   # cho phép mẫu glob trong tasks.yaml
    load_data.verify_copy(settings, cfg["inputs"])
    table, features = build_features.BUILD[cfg.get("builder", args.task)](settings.data_dir, cfg)
    rp = new_run(settings, args.task)
    out = rp.features
    write_json(out / "snapshot.json", load_data.snapshot(settings, cfg["inputs"]))
    table.to_csv(out / "table.csv.gz", index=False)
    write_json(out / "features.json", features)
    external = table.attrs.get("external")
    if external is not None:          # bảng NGOÀI cohort (không train) — chấm ở bước evaluate
        external.to_csv(out / "external.csv.gz", index=False)
    cmd = f"sky-ml build-features {args.task}"
    cards.features_card(settings, args.task, {**cfg, "inputs": patterns}, rp)
    files = [out / "table.csv.gz", out / "features.json", out / "snapshot.json"]
    if external is not None:
        files.append(out / "external.csv.gz")
    register(_catalog(settings), "features", args.task, rp.run_id, files, cmd,
             settings.features_dir.parent, {"table.csv.gz": len(table),
                                            **({"external.csv.gz": len(external)} if external is not None else {})})
    print(f"{args.task}: {len(table)} hàng, {table.subject_id.nunique()} người, {len(features)} đặc trưng → {out}")


def _train(settings, args):
    cfg = _task_cfg(settings, args.task)
    rp = resolve_run(settings, args.task, args.run)
    table = pd.read_csv(require(rp.features, "table.csv.gz", f"build-features {args.task}"))
    features = read_json(require(rp.features, "features.json", f"build-features {args.task}"))
    folds = train.make_folds(table, cfg["split"])
    save = cfg.get("save_models", {"final": True, "folds": False})
    fold_models = {} if save.get("folds") else None
    oof = train.train_predict(table, features, cfg, fold_models)
    out = ensure_writable(rp.models, settings)
    out.mkdir(parents=True, exist_ok=True)
    oof.to_csv(out / "oof.csv.gz", index=False)
    write_json(out / "folds.json",
               [{"name": str(f["name"]), "n_train": len(f["train"]), "n_test": len(f["test"])} for f in folds])
    print(f"{args.task}: {len(folds)} fold × {len(cfg['models'])} mô hình → {out / 'oof.csv.gz'}")

    entries = []
    if save.get("final", True):
        for name, model in train.train_final(table, features, cfg).items():
            info = save_model(model, out / name / "final.joblib")
            entries.append({"model": name, "kind": "final", "path": f"{name}/final.joblib",
                            "n_train_rows": len(table), "n_train_units": int(table.subject_id.nunique()), **info})
    for (fold, name), model in (fold_models or {}).items():
        safe = fold.replace(":", "_")
        info = save_model(model, out / name / "folds" / f"{safe}.joblib")
        entries.append({"model": name, "kind": fold, "path": f"{name}/folds/{safe}.joblib", **info})
    cmd = f"sky-ml train {args.task}"
    if entries:
        snap = rp.features / "snapshot.json"
        write_manifest(out, entries, {
            "task": args.task, "run_id": rp.run_id, "features": features, "target": cfg["target"],
            "seed": cfg.get("seed", 17), "model_specs": cfg["models"], "split": cfg["split"],
            "features_table": _rel(settings, rp.features / "table.csv.gz"),
            "data_snapshot": read_json(snap) if snap.exists() else None,
            "note": "final = fit trên toàn bộ người trong table; chỉ dùng cho người mới. Đánh giá dùng oof.csv.gz."})
        print(f"Đã lưu {len(entries)} mô hình → {out}")
    cards.models_card(settings, args.task, cfg, rp)
    register(_catalog(settings), "models", args.task, rp.run_id,
             [out / "oof.csv.gz", out / "folds.json"] + [out / e["path"] for e in entries]
             + ([out / "manifest.json"] if entries else []), cmd, settings.features_dir.parent,
             {"oof.csv.gz": len(oof)})


def _evaluate(settings, args):
    cfg = _task_cfg(settings, args.task)
    rp = resolve_run(settings, args.task, args.run)
    oof = pd.read_csv(require(rp.models, "oof.csv.gz", f"train {args.task}"))
    metrics = evaluate.evaluate(oof, cfg)
    best = metrics.model[0]  # chỉ để BÁO CÁO (so sánh khám phá), không dùng để chọn mô hình triển khai
    summary = {"task": args.task, "run_id": rp.run_id, "samples": int(oof.row.nunique()),
               "units": int(metrics.units[0]), "best_model_exploratory": best,
               "deploy_model": cfg.get("deploy_model"), "metrics": metrics.round(6).to_dict("records")}
    if cfg["kind"] == "regression":
        alpha = cfg.get("interval_alpha", 0.10)
        summary["interval_coverage"] = evaluate.interval_coverage(oof, best, alpha)
        if cfg.get("deploy_model") and cfg["deploy_model"] != best:
            summary["interval_coverage_deploy"] = evaluate.interval_coverage(oof, cfg["deploy_model"], alpha)
    if cfg.get("permutation_tests", 0):
        table = pd.read_csv(require(rp.features, "table.csv.gz", f"build-features {args.task}"))
        features = read_json(rp.features / "features.json")
        summary["permutation_test"] = evaluate.permutation_test(table, features, cfg, best, cfg["permutation_tests"])
    if cfg["kind"] != "regression":
        evaluate.confusion(oof, best, cfg["classes"]).to_csv(rp.models / "confusion.csv")
    metrics.to_csv(rp.models / "metrics.csv", index=False)
    write_json(rp.models / "summary.json", summary)
    if (rp.features / "external.csv.gz").exists():
        summary["external"] = _external(settings, cfg, rp, oof)
        write_json(rp.models / "summary.json", summary)
    cards.models_card(settings, args.task, cfg, rp)
    register(_catalog(settings), "models", args.task, rp.run_id,
             [rp.models / "metrics.csv", rp.models / "summary.json"], f"sky-ml evaluate {args.task}",
             settings.features_dir.parent)
    print(metrics.round(4).to_string(index=False))
    if "interval_coverage" in summary:
        cov = summary["interval_coverage"]
        print("coverage:", {k: round(v, 4) if isinstance(v, float) else v for k, v in cov.items()})


def _external(settings, cfg, rp, oof) -> dict:
    """Chấm điểm trên bảng NGOÀI cohort bằng các mô hình final (người chưa từng thấy) + ghi dự đoán deploy."""
    ext = pd.read_csv(rp.features / "external.csv.gz")
    features = read_json(rp.features / "features.json")
    train_table = pd.read_csv(rp.features / "table.csv.gz")
    n_boot, rows = cfg.get("bootstrap_samples", 10000), []
    for name in cfg["models"]:
        model = load_model(rp.models, name)
        ok = ext[features].notna().all(axis=1)
        err = (ext.loc[ok, cfg["target"]] - model.predict(ext.loc[ok, features].astype(float))).abs()
        per = err.groupby(ext.loc[ok, "subject_id"]).mean()
        lo, hi = evaluate.bootstrap_ci(per, n_boot)
        rows.append({"model": name, "units": len(per), "rows": int(ok.sum()), "mae": float(per.mean()),
                     "ci95_low": lo, "ci95_high": hi})
    pd.DataFrame(rows).to_csv(rp.models / "external_metrics.csv", index=False)
    deploy = cfg.get("deploy_model") or cfg["baseline"]
    hw = predict.calibration_half_width(oof, deploy, cfg.get("interval_alpha", 0.10), cfg["kind"])
    pred = predict.predict_rows(load_model(rp.models, deploy), ext, features, hw, train_table, cfg, deploy)
    out = ensure_writable(rp.predictions, settings)
    out.mkdir(parents=True, exist_ok=True)
    pred.to_csv(out / "external_backtest.csv", index=False)
    inside = (pred.y_true >= pred.low90) & (pred.y_true <= pred.high90)
    cov = float(inside[~pred.abstain].mean())
    cards.predictions_card(settings, rp.task, cfg, rp)
    register(_catalog(settings), "predictions", rp.task, rp.run_id, [out / "external_backtest.csv"],
             f"sky-ml evaluate {rp.task}", settings.features_dir.parent, {"external_backtest.csv": len(pred)})
    print("NGOÀI cohort:\n" + pd.DataFrame(rows).round(4).to_string(index=False) + f"\ncoverage deploy: {cov:.4f}")
    return {"metrics": rows, "deploy_model": deploy, "coverage_deploy": cov,
            "subjects": sorted(pred.subject_id.unique().tolist())}


def _predict(settings, args):
    cfg = _task_cfg(settings, args.task)
    spec = build_features.FOR_PREDICT[cfg.get("builder", args.task)]
    rp = resolve_run(settings, args.task, args.run)
    require(rp.models, "manifest.json", f"train {args.task}")
    model_name = args.model or cfg.get("deploy_model") or cfg["baseline"]
    model = load_model(rp.models, model_name)                       # kiểm SHA-256 trước khi nạp
    features = read_json(require(rp.features, "features.json", f"build-features {args.task}"))
    expected = cfg["features"] + [f"{c}_now" for c in cfg.get("context", [])] if cfg["features"] != "all" else features
    if features != expected:
        raise ValueError("configs/tasks.yaml `features` đã đổi so với lúc train run này; "
                         "chạy lại build-features + train trước khi predict.")
    train_table = pd.read_csv(require(rp.features, "table.csv.gz", f"build-features {args.task}"))
    oof = pd.read_csv(require(rp.models, "oof.csv.gz", f"train {args.task}"))
    half_width = predict.calibration_half_width(oof, model_name, cfg.get("interval_alpha", 0.10), cfg["kind"])

    source = Path(args.input)
    args.mode = args.mode or ("latest" if "latest" in spec else "table")
    raw = None
    if args.mode == "table":
        raw = pd.read_csv(source)
        rows = predict.table_rows(raw, cfg)
    elif args.mode in spec:
        cols = spec["columns"] + cfg.get("context", []) if spec.get("columns") else None
        raw = pd.read_csv(source, usecols=cols)
        rows = spec[args.mode](raw, cfg)
    else:
        raise ValueError(f"Task {args.task} không hỗ trợ --mode {args.mode}; dùng: {['table', *spec.keys() - {'columns'}]}")
    result = predict.predict_rows(model, rows, features, half_width, train_table, cfg, model_name)
    if raw is None:
        raw = pd.read_csv(source)
    synthetic = set(raw.loc[raw["is_synthetic"].astype(bool), "subject_id"]) if {"is_synthetic", "subject_id"} <= set(raw) else set()
    result["input_synthetic"] = result.subject_id.isin(synthetic)   # đầu vào là DỮ LIỆU GIẢ ĐỊNH

    out = ensure_writable(rp.predictions, settings)
    out.mkdir(parents=True, exist_ok=True)
    tag = "_SYNTHETIC-INPUT" if result.input_synthetic.any() else ""
    stem = f"{source.name.split('.')[0]}_{args.mode}_{model_name}{tag}_{datetime.now():%Y%m%d_%H%M%S}"
    result.to_csv(out / f"{stem}.csv", index=False)
    meta = {"task": args.task, "run_id": rp.run_id, "model": model_name, "mode": args.mode,
            "input": str(source), "half_width_90": half_width if math.isfinite(half_width) else None, "n_rows": len(result),
            "n_abstain": int(result.abstain.sum()), "n_in_sample": int(result.in_sample.sum()),
            "n_input_synthetic": int(result.input_synthetic.sum())}
    if "abs_error" in result:
        meta["mae_backtest"] = float(result.abs_error.mean())
    if "correct" in result:
        meta["accuracy_backtest"] = float(result.correct[~result.abstain].mean())
    write_json(out / f"{stem}.json", meta)

    cmd = f"sky-ml predict {args.task} --input {source.name} --mode {args.mode}"
    cards.predictions_card(settings, args.task, cfg, rp)
    register(_catalog(settings), "predictions", args.task, rp.run_id, [out / f"{stem}.csv", out / f"{stem}.json"],
             cmd, settings.features_dir.parent, {f"{stem}.csv": len(result)})
    print(result.head(10).to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in meta.items()})
    print(f"→ {out / (stem + '.csv')}")
    if meta["n_in_sample"]:
        print("CHÚ Ý: có người đã nằm trong dữ liệu huấn luyện (in_sample=True) — không phải đánh giá trên người mới.")

if __name__ == "__main__":
    main()
