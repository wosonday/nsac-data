
import pytest

from sky_ml._steps import load_data

copy_data, verify_copy = load_data.copy_data, load_data.verify_copy


def test_copies_and_verifies(settings):
    df = copy_data(settings)
    assert set(df.status) == {"copied"}
    assert df.set_index("rel_path").loc["processed/sample-v2/mmash_minutes.csv.gz", "hash_source"] == "nasa_cl_manifest"


def test_second_run_skips(settings):
    copy_data(settings)
    assert set(copy_data(settings).status) == {"skipped_ok"}


def test_hash_mismatch_removes_dst(settings, fake_src):
    (fake_src / "processed/sample-v2/mmash_minutes.csv.gz").write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="sha256"):
        copy_data(settings)
    assert not any(settings.data_dir.rglob("*.csv.gz"))


def test_copy_interrupted_leaves_no_partial(settings, monkeypatch):
    def boom(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(load_data.os, "replace", boom)
    with pytest.raises(OSError):
        copy_data(settings)
    assert not [p for p in settings.data_dir.rglob("*") if p.is_file()]


def test_dry_run_writes_nothing(settings):
    copy_data(settings, dry_run=True)
    assert not settings.data_dir.exists()


REL = "processed/sample-v2/mmash_minutes.csv.gz"


def test_check_passes_after_copy(settings):
    copy_data(settings)
    assert verify_copy(settings) == 2


def test_check_detects_modified_file(settings):
    copy_data(settings)
    with open(settings.data_dir / REL, "ab") as f:
        f.write(b"x")
    with pytest.raises(ValueError, match="mmash_minutes"):
        verify_copy(settings)
