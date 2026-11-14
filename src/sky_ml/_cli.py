"""Hỗ trợ (ngoài luồng): dòng lệnh `sky-ml`. Mỗi lệnh con ứng với một bước đánh số trong _steps.STEPS.

File trong runs/<task>/<run>/ mang số của bước đã tạo ra nó:
2_* (build-features), 3_* (train), 4_* (evaluate), 5_predictions/ (predict).
"""
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

from ._artifacts import load_model, save_model, write_manifest
from ._jsonio import read_json, write_json
from ._runs import new_run, require, resolve_run
from ._settings import load_settings, load_tasks
from ._steps import STEPS, build_features, evaluate, load_data, predict, train


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sky-ml")
    parser.add_argument("--config", default="sky_ml.yaml")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("steps", help="in thứ tự các bước pipeline")
    sub.add_parser("load-data", help=STEPS[1][2]).add_argument("--dry-run", action="store_true")
    sub.add_parser("check", help="(bước 1) kiểm bản copy còn khớp data/COPY_MANIFEST.csv")
    sub.add_parser("build-features", help=STEPS[2][2]).add_argument("task", choices=sorted(build_features.BUILD))
    for name, number in (("train", 3), ("evaluate", 4)):
        p = sub.add_parser(name, help=STEPS[number][2])
        p.add_argument("task")
        p.add_argument("--run", default="latest", help="tên thư mục run hoặc 'latest'")
    p = sub.add_parser("predict", help=STEPS[5][2])
    p.add_argument("task")
    p.add_argument("--input", required=True, help="CSV dữ liệu MỚI, cùng cột với dữ liệu gốc của task")
    p.add_argument("--run", default="latest", help="run chứa mô hình đã huấn luyện (3_models)")
    p.add_argument("--model", default=None, help="tên mô hình; mặc định = deploy_model trong tasks.yaml")
    p.add_argument("--mode", choices=["latest", "backtest"], default="latest")
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


def _build_features(settings, args):
    cfg = load_tasks(settings)[args.task]
    load_data.verify_copy(settings, cfg["inputs"])
    table, features = build_features.BUILD[args.task](settings.data_dir, cfg)
    run = new_run(settings, args.task)
    write_json(run / "2_snapshot.json", load_data.snapshot(settings, cfg["inputs"]))
    table.to_csv(run / "2_table.csv.gz", index=False)
    write_json(run / "2_features.json", features)
    print(f"{args.task}: {len(table)} hàng, {table.subject_id.nunique()} người, {len(features)} đặc trưng → {run}")


def _train(settings, args):
    cfg = load_tasks(settings)[args.task]
    run = resolve_run(settings, args.task, args.run)
    table = pd.read_csv(require(run, "2_table.csv.gz", f"build-features {args.task}"))
    features = read_json(require(run, "2_features.json", f"build-features {args.task}"))
    folds = train.make_folds(table, cfg["split"])
    save = cfg.get("save_models", {"final": True, "folds": False})
    fold_models = {} if save.get("folds") else None
    oof = train.train_predict(table, features, cfg, fold_models)
    oof.to_csv(run / "3_oof.csv.gz", index=False)
    write_json(run / "3_folds.json",
               [{"name": str(f["name"]), "n_train": len(f["train"]), "n_test": len(f["test"])} for f in folds])
    print(f"{args.task}: {len(folds)} fold × {len(cfg['models'])} mô hình → {run / '3_oof.csv.gz'}")

    entries, models_dir = [], run / "3_models"
    if save.get("final", True):
        for name, model in train.train_final(table, features, cfg).items():
            info = save_model(model, models_dir / name / "final.joblib")
            entries.append({"model": name, "kind": "final", "path": f"{name}/final.joblib",
                            "n_train_rows": len(table), "n_train_units": int(table.subject_id.nunique()), **info})
    for (fold, name), model in (fold_models or {}).items():
        safe = fold.replace(":", "_")
        info = save_model(model, models_dir / name / "folds" / f"{safe}.joblib")
        entries.append({"model": name, "kind": fold, "path": f"{name}/folds/{safe}.joblib", **info})
    if entries:
        snap = run / "2_snapshot.json"
        write_manifest(models_dir, entries, {
            "task": args.task, "features": features, "target": cfg["target"], "seed": cfg.get("seed", 17),
            "model_specs": cfg["models"], "split": cfg["split"],
            "data_snapshot": read_json(snap) if snap.exists() else None,
            "note": "final = fit trên toàn bộ người trong table; chỉ dùng cho người mới. Đánh giá dùng 3_oof.csv.gz."})
        print(f"Đã lưu {len(entries)} mô hình → {models_dir}")


def _evaluate(settings, args):
    cfg = load_tasks(settings)[args.task]
    run = resolve_run(settings, args.task, args.run)
    oof = pd.read_csv(require(run, "3_oof.csv.gz", f"train {args.task}"))
    metrics = evaluate.evaluate(oof, cfg)
    best = metrics.model[0]  # chỉ để BÁO CÁO (so sánh khám phá), không dùng để chọn mô hình triển khai
    summary = {"task": args.task, "samples": int(oof.row.nunique()), "units": int(metrics.units[0]),
               "best_model_exploratory": best, "deploy_model": cfg.get("deploy_model"),
               "metrics": metrics.round(6).to_dict("records")}
    if cfg["kind"] == "regression":
        summary["interval_coverage"] = evaluate.interval_coverage(oof, best, cfg.get("interval_alpha", 0.10))
    else:
        evaluate.confusion(oof, best, cfg["classes"]).to_csv(run / "4_confusion.csv")
    metrics.to_csv(run / "4_metrics.csv", index=False)
    write_json(run / "4_summary.json", summary)
    print(metrics.round(4).to_string(index=False))
    if "interval_coverage" in summary:
        cov = summary["interval_coverage"]
        print("coverage:", {k: round(v, 4) if isinstance(v, float) else v for k, v in cov.items()})


def _predict(settings, args):
    cfg = load_tasks(settings)[args.task]
    spec = build_features.FOR_PREDICT[args.task]
    run = resolve_run(settings, args.task, args.run)
    models_dir = require(run, "3_models", f"train {args.task}")
    model_name = args.model or cfg.get("deploy_model") or cfg["baseline"]
    model = load_model(models_dir, model_name)                      # kiểm SHA-256 trước khi nạp
    features = read_json(require(run, "2_features.json", f"build-features {args.task}"))
    if features != cfg["features"]:
        raise ValueError("configs/tasks.yaml `features` đã đổi so với lúc train run này; "
                         "chạy lại build-features + train trước khi predict.")
    train_table = pd.read_csv(require(run, "2_table.csv.gz", f"build-features {args.task}"))
    oof = pd.read_csv(require(run, "3_oof.csv.gz", f"train {args.task}"))
    half_width = predict.calibration_half_width(oof, model_name, cfg.get("interval_alpha", 0.10))

    source = Path(args.input)
    rows = spec[args.mode](pd.read_csv(source, usecols=spec["columns"]), cfg)
    result = predict.predict_rows(model, rows, features, half_width, train_table, cfg, model_name)

    out_dir = run / "5_predictions"
    out_dir.mkdir(exist_ok=True)
    stem = f"{source.name.split('.')[0]}_{args.mode}_{model_name}_{datetime.now():%Y%m%d_%H%M%S}"
    result.to_csv(out_dir / f"{stem}.csv", index=False)
    meta = {"task": args.task, "run": run.name, "model": model_name, "mode": args.mode, "input": str(source),
            "half_width_90": half_width, "n_rows": len(result), "n_abstain": int(result.abstain.sum()),
            "n_in_sample": int(result.in_sample.sum())}
    if "abs_error" in result:
        meta["mae_backtest"] = float(result.abs_error.mean())
    write_json(out_dir / f"{stem}.json", meta)
    print(result.head(10).round(2).to_string(index=False))
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in meta.items()})
    print(f"→ {out_dir / (stem + '.csv')}")
    if meta["n_in_sample"]:
        print("CHÚ Ý: có người đã nằm trong dữ liệu huấn luyện (in_sample=True) — không phải đánh giá trên người mới.")


if __name__ == "__main__":
    main()
