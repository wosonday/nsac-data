import pytest

from sky_ml.settings import Settings, ensure_writable, load_settings, load_tasks


def test_env_overrides_source(tmp_path, monkeypatch):
    cfg = tmp_path / "sky_ml.yaml"
    cfg.write_text(
        "nasa_cl_data: X\ndata_dir: data\nruns_dir: runs\ntasks_config: configs/tasks.yaml\n"
    )
    monkeypatch.setenv("SKY_NASA_CL_DATA", str(tmp_path / "src"))
    s = load_settings(cfg)
    assert s.nasa_cl_data == tmp_path / "src" and s.data_dir == tmp_path / "data"
    assert s.tasks_config == tmp_path / "configs/tasks.yaml"


def test_refuses_output_inside_source(tmp_path):
    s = Settings(
        tmp_path / "ncl", tmp_path / "data", tmp_path / "runs", tmp_path / "t.yaml"
    )
    with pytest.raises(ValueError, match="NASA-cl"):
        ensure_writable(tmp_path / "ncl" / "runs", s)


def test_repo_tasks_yaml_is_valid():
    """configs/tasks.yaml của repo phải đọc được và có đủ khóa bắt buộc."""
    from pathlib import Path

    s = load_settings(Path(__file__).parents[1] / "sky_ml.yaml")
    hr = load_tasks(s)["hr"]
    assert hr["window"] == {"past": 30, "future": 5, "step": 5} and hr[
        "valid_hr_range"
    ] == [30.0, 220.0]
