import pytest

from tests.blender_harness import run_blender_script

NEW = ("table", "chair", "shelf", "lamppost", "fence", "crate", "barrel", "stairs",
       "detached_house", "rowhouse", "apartment", "cabin", "barn",
       "brownstone", "victorian", "tudor", "craftsman", "colonial_revival", "art_deco_tower", "haussmann",
       "warehouse", "church", "shopfront_block")


@pytest.mark.blender
@pytest.mark.parametrize("name", NEW)
def test_generic_contract(name):
    run_blender_script("new_builders_check.py", "generic:" + name)


@pytest.mark.blender
@pytest.mark.parametrize("name", NEW)
def test_param_effect(name):
    run_blender_script("new_builders_check.py", "specific:" + name)
