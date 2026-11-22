import pytest

from tests.blender_harness import run_blender_script


def _run(name):
    run_blender_script("builders_check.py", name)


@pytest.mark.blender
def test_house_deterministic():
    _run("house_deterministic")


@pytest.mark.blender
def test_house_all_tags_present_and_under_budget():
    _run("house_budget")


@pytest.mark.blender
def test_house_has_pan_and_cover_tiles():
    _run("house_pan_cover")


@pytest.mark.blender
def test_house_roof_sags():
    _run("house_sag")


@pytest.mark.blender
def test_house_openings_are_open():
    _run("house_openings")


@pytest.mark.blender
def test_cabinet_dimensions_follow_params():
    _run("cabinet_dims")


@pytest.mark.blender
def test_shots_named():
    _run("shots")


@pytest.mark.blender
def test_phonebooth_dimensions_and_glazing_toggle():
    _run("phonebooth_dims")
