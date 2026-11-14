"""End-to-end trên dữ liệu giả: 3 nhóm dữ liệu được tạo đúng chỗ, có README và có trong CATALOG."""
import csv

from sky_ml._cli import main
from sky_ml._runs import resolve_run
from sky_ml._steps import load_data


def test_three_data_groups_documented(settings, config_file, tmp_path):
    load_data.copy_data(settings)
    for cmd in (["build-features", "hr"], ["train", "hr"], ["evaluate", "hr"]):
        main(["--config", str(config_file), *cmd])
    src = settings.data_dir / "processed/sample-v2/mmash_minutes.csv.gz"
    main(["--config", str(config_file), "predict", "hr", "--input", str(src)])
    rp = resolve_run(settings, "hr")

    assert (rp.features / "table.csv.gz").exists()                       # (1) đầu vào mô hình
    assert (rp.models / "ridge" / "final.joblib").exists()               # (3) mô hình
    assert (rp.models / "metrics.csv").exists() and (rp.models / "oof.csv.gz").exists()
    assert list(rp.predictions.glob("*.csv"))                            # (2) dự đoán
    for folder, title in ((rp.features, "(1)"), (rp.models, "(3)"), (rp.predictions, "(2)")):
        assert title in (folder / "README.md").read_text(encoding="utf-8")

    with open(settings.features_dir.parent / "CATALOG.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert {r["kind"] for r in rows} == {"features", "models", "predictions"}
    assert all(len(r["sha256"]) == 64 and r["run_id"] == rp.run_id for r in rows)
    model_card = (rp.models / "README.md").read_text(encoding="utf-8")
    assert "mae – ridge" in model_card and "Độ bao phủ" in model_card
    readme = (settings.features_dir.parent / "README.md").read_text(encoding="utf-8")
    assert "<!-- CATALOG:START -->" in readme and f"`{rp.run_id}`" in readme
    assert readme.count("2_features/hr/") >= 3                         # mỗi file features một dòng
