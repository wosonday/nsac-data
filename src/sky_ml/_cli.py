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

from ._artifacts import load_model, save_model, write_manifest
from ._datacards import register, write_card
from ._jsonio import read_json, write_json
from ._runs import new_run, require, resolve_run
from ._settings import ensure_writable, load_dictionary, load_settings, load_tasks
from ._steps import STEPS, build_features, evaluate, load_data, predict, train


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sky-ml")
    parser.add_argument("--config", default="sky_ml.yaml")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("steps", help="in thứ tự các bước pipeline")
    sub.add_parser("load-data", help=STEPS[1][2]).add_argument("--dry-run", action="store_true")
    sub.add_parser("check", help="(bước 1) kiểm bản copy còn khớp data/COPY_MANIFEST.csv")
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
     "evaluate": _evaluate, "predict": _predict}[args.command](settings, args)


def _load_data(settings, args):
    table = load_data.copy_data(settings, dry_run=args.dry_run)
    if not args.dry_run:
        print(table.status.value_counts().to_string(), f"\n→ {settings.data_dir}")
        print(f"check: OK {load_data.verify_copy(settings)} files")


def _check(settings, args):
    print(f"OK {load_data.verify_copy(settings)} files")


def _task_cfg(settings, task):
    tasks = load_tasks(settings)
    if task not in tasks:
        raise SystemExit(f"Task '{task}' không có trong {settings.tasks_config}; có: {', '.join(tasks)}")
    return tasks[task]


def _catalog(settings):
    return settings.features_dir.parent / "CATALOG.csv"


def _rel(settings, path) -> str:
    """Đường dẫn tương đối so với thư mục data/ (để README không phụ thuộc máy)."""
    try:
        return "data/" + Path(path).resolve().relative_to(settings.features_dir.parent.resolve()).as_posix()
    except ValueError:
        return str(path)


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
    cmd = f"sky-ml build-features {args.task}"
    write_card(out, "features", args.task, rp.run_id, load_dictionary(settings), unit=cfg.get("unit"),
               produced_by=cmd, columns=list(table.columns),
               files={"table.csv.gz": "Bảng mẫu: subject_id, cutoff_time, đặc trưng, target",
                      "features.json": "Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml)",
                      "snapshot.json": "SHA-256 file nguồn + phiên bản thư viện + seed (tái lập)"},
               facts={"Số hàng (mẫu)": len(table), "Số người/chuỗi độc lập": table.subject_id.nunique(),
                      "Số đặc trưng": len(features), "Target": f"`{cfg['target']}` ({cfg.get('unit')})",
                      "Cửa sổ": cfg.get("window")},
               lineage={"Dữ liệu nguồn": ", ".join(f"data/1_source/{p}" for p in patterns), "Mô hình dùng bảng này": _rel(settings, rp.models)})
    register(_catalog(settings), "features", args.task, rp.run_id,
             [out / "table.csv.gz", out / "features.json", out / "snapshot.json"], cmd,
             settings.features_dir.parent, {"table.csv.gz": len(table)})
    print(f"{args.task}: {len(table)} hàng, {table.subject_id.nunique()} người, {len(features)} đặc trưng → {out}")


def _model_card(settings, cfg, rp, cmd, facts):
    files = {"oof.csv.gz": "Dự đoán ngoài tập huấn luyện (OOF) của mọi mô hình — nguồn của mọi điểm đánh giá",
             "folds.json": "Danh sách fold và số mẫu train/test", "manifest.json": "SHA-256 + phiên bản + tham số",
             "<model>/final.joblib": "Mô hình fit trên toàn bộ người → chỉ dùng cho NGƯỜI MỚI"}
    if (rp.models / "metrics.csv").exists():
        files["metrics.csv"] = "Metric theo người, CI95, so baseline"
        files["summary.json"] = "Tóm tắt + độ bao phủ khoảng 90%"
    write_card(rp.models, "models", rp.task, rp.run_id, load_dictionary(settings), unit=cfg.get("unit"),
               produced_by=cmd, files=files, facts=facts,
               columns=["fold", "row", "subject_id", "model", "y_true", "y_pred"],
               lineage={"Bảng đặc trưng (đầu vào)": _rel(settings, rp.features / "table.csv.gz"),
                        "Dự đoán từ các mô hình này": _rel(settings, rp.predictions)},
               extra=["## Cảnh báo bảo mật", "",
                      ("File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` "
                       "(kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.")])


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
    _model_card(settings, cfg, rp, cmd, {"Số fold": len(folds), "Mô hình": ", ".join(cfg["models"]),
                                         "Mô hình triển khai (deploy_model)": cfg.get("deploy_model"),
                                         "Số file mô hình": len(entries)})
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
    metric = "mae" if cfg["kind"] == "regression" else "macro_f1"
    facts = {f"{metric} – {r['model']}": f"{r[metric]:.4f} (CI95 {r['ci95_low']:.3f}–{r['ci95_high']:.3f}); "
             f"so baseline {r['diff_vs_baseline']:+.3f}" for r in summary["metrics"]}
    if "permutation_test" in summary:
        pt = summary["permutation_test"]
        facts["Kiểm định hoán vị"] = f"{pt['model']}: p = {pt['p_value']:.4f} ({pt['n_permutations']} lần)"
    if "interval_coverage" in summary:
        cov = summary["interval_coverage"]
        facts["Độ bao phủ khoảng 90%"] = f"{cov['observed_coverage']:.4f} (nửa độ rộng {cov['median_half_width']:.3f})"
    facts["Đơn vị độc lập"] = int(metrics.units[0])
    _model_card(settings, cfg, rp, f"sky-ml train/evaluate {args.task}", facts)
    register(_catalog(settings), "models", args.task, rp.run_id,
             [rp.models / "metrics.csv", rp.models / "summary.json"], f"sky-ml evaluate {args.task}",
             settings.features_dir.parent)
    print(metrics.round(4).to_string(index=False))
    if "interval_coverage" in summary:
        cov = summary["interval_coverage"]
        print("coverage:", {k: round(v, 4) if isinstance(v, float) else v for k, v in cov.items()})


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
    if args.mode == "table":
        rows = predict.table_rows(pd.read_csv(source), cfg)
    elif args.mode in spec:
        rows = spec[args.mode](pd.read_csv(source, usecols=spec["columns"] + cfg.get("context", [])), cfg)
    else:
        raise ValueError(f"Task {args.task} không hỗ trợ --mode {args.mode}; dùng: {['table', *spec.keys() - {'columns'}]}")
    result = predict.predict_rows(model, rows, features, half_width, train_table, cfg, model_name)

    out = ensure_writable(rp.predictions, settings)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{source.name.split('.')[0]}_{args.mode}_{model_name}_{datetime.now():%Y%m%d_%H%M%S}"
    result.to_csv(out / f"{stem}.csv", index=False)
    meta = {"task": args.task, "run_id": rp.run_id, "model": model_name, "mode": args.mode,
            "input": str(source), "half_width_90": half_width if math.isfinite(half_width) else None, "n_rows": len(result),
            "n_abstain": int(result.abstain.sum()), "n_in_sample": int(result.in_sample.sum())}
    if "abs_error" in result:
        meta["mae_backtest"] = float(result.abs_error.mean())
    if "correct" in result:
        meta["accuracy_backtest"] = float(result.correct[~result.abstain].mean())
    write_json(out / f"{stem}.json", meta)

    cmd = f"sky-ml predict {args.task} --input {source.name} --mode {args.mode}"
    listing = sorted(p.name for p in out.glob("*.csv"))
    write_card(out, "predictions", args.task, rp.run_id, load_dictionary(settings), unit=cfg.get("unit"),
               produced_by="sky-ml predict", columns=list(result.columns),
               files={**{n: "Dự đoán (mỗi lần chạy predict một file; .json cùng tên = thông tin lần chạy)"
                         for n in listing}},
               facts={"Lần chạy mới nhất": stem, "Mô hình": model_name, "Chế độ": args.mode,
                      "Số hàng": len(result), "Từ chối (abstain)": meta["n_abstain"],
                      "Trong dữ liệu huấn luyện (in_sample)": meta["n_in_sample"],
                      "Nửa độ rộng khoảng 90%": (f"{half_width:.3f} {cfg.get('unit') or ''}"
                                                 if cfg["kind"] == "regression" else "— (phân loại)")},
               lineage={"Mô hình": _rel(settings, rp.models / model_name / "final.joblib"),
                        "Bảng đặc trưng của run": _rel(settings, rp.features / "table.csv.gz")})
    register(_catalog(settings), "predictions", args.task, rp.run_id, [out / f"{stem}.csv", out / f"{stem}.json"],
             cmd, settings.features_dir.parent, {f"{stem}.csv": len(result)})
    print(result.head(10).to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in meta.items()})
    print(f"→ {out / (stem + '.csv')}")
    if meta["n_in_sample"]:
        print("CHÚ Ý: có người đã nằm trong dữ liệu huấn luyện (in_sample=True) — không phải đánh giá trên người mới.")

if __name__ == "__main__":
    main()
