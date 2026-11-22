import pytest

from tests.blender_harness import run_blender_script


@pytest.mark.blender
def test_tiling():
    """Covers seamless wood/stone tiles, UV scale, grain-aware UVs and cache reuse."""
    run_blender_script("tiling_check.py")
