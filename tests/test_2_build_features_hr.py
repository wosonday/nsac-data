
import numpy as np
import pytest

from sky_ml._cli import main
from sky_ml._steps import load_data

copy_data = load_data.copy_data
from sky_ml._steps import build_features

W = build_features.windows
NAMES = list(W.FEATURES)[:7]
from sky_ml._runs import resolve_run


def test_windows_use_only_past():
    t = W.make_windows(np.arange(40, dtype=float), np.arange(40), past=30, future=5, step=5, names=NAMES)
    assert t.iloc[0].last_value == 29 and t.iloc[0].target == np.mean([30, 31, 32, 33, 34])


def test_window_touching_nan_is_dropped():
    v = np.arange(40, dtype=float)
    v[31] = np.nan
    assert len(W.make_windows(v, np.arange(40), 30, 5, 5, NAMES)) == 0


def test_latest_missing_raises_hint(settings):
    with pytest.raises(FileNotFoundError, match="sky-ml build-features hr"):
        resolve_run(settings, "hr", "latest")


def test_build_features_writes_card_and_catalog(settings, config_file):
    copy_data(settings)
    main(["--config", str(config_file), "build-features", "hr"])
    rp = resolve_run(settings, "hr")
    assert {"table.csv.gz", "features.json", "snapshot.json", "README.md"} <= {p.name for p in rp.features.iterdir()}
    card = (rp.features / "README.md").read_text(encoding="utf-8")
    assert "(1) Dữ liệu đã xử lý" in card and "`last_value`" in card and "bpm" in card
    catalog = (settings.features_dir.parent / "CATALOG.csv").read_text(encoding="utf-8")
    assert "features,hr," in catalog and "2_features/hr/" in catalog


def test_unknown_feature_in_config_rejected():
    import pytest
    with pytest.raises(ValueError, match="không tồn tại"):
        W.check_features(["last_value", "khong_co"])


def test_feature_selection_follows_config():
    t = W.make_windows(np.arange(40, dtype=float), np.arange(40), 30, 5, 5, ["last_value", "slope_all"])
    assert list(t.columns) == ["cutoff_time", "last_value", "slope_all", "target"]
    assert t.iloc[0].slope_all == pytest.approx(1.0)
