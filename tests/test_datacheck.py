import pytest

from sky_ml.copydata import copy_data
from sky_ml.datacheck import verify_copy

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
