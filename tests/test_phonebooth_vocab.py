import pytest

from rbxasset import match
from rbxasset.builders import load_vocab

V = load_vocab("phonebooth")
OK = {k: d.default for k, d in V.params.items()}


def test_defaults_validate():
    V.validate(OK, {})


@pytest.mark.parametrize("bad", [
    {"width": 0.5}, {"height": 30}, {"pane_cols": 0}, {"pane_rows": 2.5}, {"pane_cols": True},
    {"roof_rise": 5.0},
])
def test_bad_params_rejected(bad):
    with pytest.raises(ValueError):
        V.validate({**OK, **bad}, {})


def test_matcher_finds_phonebooth_and_still_declines_others():
    r = match.registered_vocabs()
    for words in ("phonebooth", "red telephone box", "phone kiosk"):
        ms = match.match_all(words, r)
        assert (ms[0].builder, match.verdict(ms)[0]) == ("phonebooth", "build"), words
    assert match.verdict(match.match_all("photo booth", r))[0] == "decline"
    assert match.match_all("sideboard", r)[0].builder == "cabinet"
