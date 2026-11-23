import pytest

from rbxasset.builders import load_vocab

BAD = {
    "table": [
        {"width": 0.1},
        {"leg_shape": "oval"},
        {"top_thickness": 2.0},
        {"apron_height": -1},
    ],
    "chair": [
        {"back_style": "wing"},
        {"slat_count": 0},
        {"seat_height": 9},
        {"seat_width": True},
    ],
    "shelf": [{"shelf_count": 0}, {"shelf_count": 12, "height": 3.0}, {"depth": 0.1}],
    "lamppost": [
        {"head_style": "gas"},
        {"height": 1.0},
        {"arm_length": -1},
        {"height": 3.0, "base_height": 2.9},
    ],
    "fence": [
        {"picket_style": "round"},
        {"rail_count": 0},
        {"post_spacing": 99},
        {"length": 1},
    ],
    "crate": [{"board_count": 1}, {"board_count": 10, "height": 0.7}, {"width": 0}],
    "barrel": [{"hoop_count": 1}, {"wall": 0.5}, {"bulge": 2}],
    "stairs": [
        {"steps": 0},
        {"tread_thickness": 0.9, "rise": 0.5},
        {"run": 0.1},
        {"steps": 2.5},
    ],
}


def defaults(name):
    return {k: d.default for k, d in load_vocab(name).params.items()}


@pytest.mark.parametrize("name", sorted(BAD))
def test_defaults_validate(name):
    load_vocab(name).validate(defaults(name), {})


@pytest.mark.parametrize(
    "name,bad",
    [(n, b) for n, bs in sorted(BAD.items()) for b in bs],
    ids=lambda v: str(v),
)
def test_bad_params_rejected(name, bad):
    with pytest.raises(ValueError):
        load_vocab(name).validate({**defaults(name), **bad}, {})
