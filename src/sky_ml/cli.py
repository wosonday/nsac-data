"""sky-ml copy-data | check | prepare <task> | train <task> | evaluate <task>"""
import argparse
import json

import pandas as pd

from .artifacts import save_model, write_manifest
from .copydata import copy_data
from .datacheck import snapshot, verify_copy
from .evaluate import confusion, evaluate, interval_coverage
from .prepare import PREPARE
from .runs import new_run, require, resolve_run
from .settings import load_settings, load_tasks
from .train import make_folds, train_final, train_predict


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sky-ml")
    parser.add_argument("--config", default="sky_ml.yaml")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("copy-data").add_argument("--dry-run", action="store_true")
    sub.add_parser("check")
    sub.add_parser("prepare").add_argument("task", choices=sorted(PREPARE))
    for name in ("train", "evaluate"):
        p = sub.add_parser(name)
        p.add_argument("task")
        p.add_argument("--run", default="latest", help="tên thư mục run hoặc 'latest'")
    args = parser.parse_args(argv)
    settings = load_settings(args.config)

    if args.command == "copy-data":
        table = copy_data(settings, dry_run=args.dry_run)
        if not args.dry_run:
            print(table.status.value_counts().to_string(), f"\n→ {settings.data_dir}")
    elif args.command == "check":
        print(f"OK {verify_copy(settings)} files")
    elif args.command == "prepare":
        cfg = load_tasks(settings)[args.task]
        verify_copy(settings, cfg["inputs"])
        table, features = PREPARE[args.task](settings.data_dir, cfg)
        run = new_run(settings, args.task)
        table.to_csv(run / "table.csv.gz", index=False)
        (run / "features.json").write_text(json.dumps(features, indent=2))
        (run / "snapshot.json").write_text(json.dumps(snapshot(settings, cfg["inputs"]), indent=2))
        print(f"{args.task}: {len(table)} hàng, {table.subject_id.nunique()} người → {run}")
    elif args.command == "train":
        cfg = load_tasks(settings)[args.task]
        run = resolve_run(settings, args.task, args.run)
        table = pd.read_csv(require(run, "table.csv.gz", f"prepare {args.task}"))
        features = json.loads(require(run, "features.json", f"prepare {args.task}").read_text())
        folds = make_folds(table, cfg["split"])
        save = cfg.get("save_models", {"final": True, "folds": False})
        fold_models = {} if save.get("folds") else None
        oof = train_predict(table, features, cfg, fold_models)
        oof.to_csv(run / "oof.csv.gz", index=False)
        entries, models_dir = [], run / "models"
        if save.get("final", True):
            for name, model in train_final(table, features, cfg).items():
                info = save_model(model, models_dir / name / "final.joblib")
                entries.append({"model": name, "kind": "final", "path": f"{name}/final.joblib",
                                "n_train_rows": len(table), "n_train_units": int(table.subject_id.nunique()), **info})
        for (fold, name), model in (fold_models or {}).items():
            safe = fold.replace(":", "_")
            info = save_model(model, models_dir / name / "folds" / f"{safe}.joblib")
            entries.append({"model": name, "kind": fold, "path": f"{name}/folds/{safe}.joblib", **info})
        if entries:
            write_manifest(models_dir, entries, {
                "task": args.task, "features": features, "target": cfg["target"], "seed": cfg.get("seed", 17),
                "model_specs": cfg["models"], "split": cfg["split"],
                "data_snapshot": json.loads((run / "snapshot.json").read_text()) if (run / "snapshot.json").exists() else None,
                "note": "final = fit trên toàn bộ người trong table; chỉ dùng cho người mới. Đánh giá dùng oof.csv.gz."})
            print(f"Đã lưu {len(entries)} mô hình → {models_dir}")
        (run / "folds.json").write_text(json.dumps(
            [{"name": str(f["name"]), "n_train": len(f["train"]), "n_test": len(f["test"])} for f in folds], indent=2))
        print(f"{args.task}: {len(folds)} fold × {len(cfg['models'])} mô hình → {run / 'oof.csv.gz'}")
    elif args.command == "evaluate":
        cfg = load_tasks(settings)[args.task]
        run = resolve_run(settings, args.task, args.run)
        oof = pd.read_csv(require(run, "oof.csv.gz", f"train {args.task}"))
        metrics = evaluate(oof, cfg)
        best = metrics.model[0]   # chỉ để BÁO CÁO (so sánh khám phá), không dùng để chọn mô hình triển khai
        summary = {"task": args.task, "samples": int(oof.row.nunique()), "units": int(metrics.units[0]),
                   "best_model_exploratory": best, "metrics": metrics.round(6).to_dict("records")}
        if cfg["kind"] == "regression":
            summary["interval_coverage"] = interval_coverage(oof, best, cfg.get("interval_alpha", 0.10))
        else:
            confusion(oof, best, cfg["classes"]).to_csv(run / "confusion.csv")
        metrics.to_csv(run / "metrics.csv", index=False)
        (run / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
        print(metrics.round(4).to_string(index=False))
        if "interval_coverage" in summary:
            print("coverage:", {k: round(v, 4) if isinstance(v, float) else v for k, v in summary["interval_coverage"].items()})


if __name__ == "__main__":
    main()
