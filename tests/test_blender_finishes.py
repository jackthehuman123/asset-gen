import pytest

from tests.blender_harness import run_blender_script


@pytest.mark.blender
def test_finishes_build_and_render():
    run_blender_script("finishes_check.py")
