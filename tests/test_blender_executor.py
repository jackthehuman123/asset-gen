import pytest

from tests.blender_harness import run_blender_script


def _run(name):
    run_blender_script("executor_check.py", name)


@pytest.mark.blender
def test_join_one_mesh_per_tag_with_finish():
    _run("join")


@pytest.mark.blender
def test_budget_guard_names_tag():
    _run("budget")


@pytest.mark.blender
def test_bake_sizes_and_metalness():
    _run("bake")


@pytest.mark.blender
def test_tiled_tag_uses_shared_tile():
    _run("tiled")


@pytest.mark.blender
def test_export_fbx_exists_and_reimports_with_same_tris():
    _run("fbx")
