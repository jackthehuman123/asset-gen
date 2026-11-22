import pytest

from rbxasset import cli, match
from rbxasset.builders.vocab import Vocab


def vocab(makes, not_for=("nothing",)):
    return Vocab(params={}, part_tags=(), tiled_tags=frozenset(), big_tags=frozenset(),
                 no_collide_tags=frozenset(), makes=tuple(makes), not_for=tuple(not_for))


V = {"cabinet": vocab(["cabinet", "sideboard"], ["cup cabinet", "locker"]),
     "house": vocab(["house", "cottage"], ["tower"])}


def top(request, vocabs=V):
    ms = match.match_all(request, vocabs)
    return ms[0], match.verdict(ms)[0]


def test_plain_fit_builds():
    m, v = top("a sideboard")
    assert (m.builder, m.confidence, v) == ("cabinet", 1.0, "build")


def test_plural_and_case_and_hyphen_are_normalised():
    assert top("Cottages")[0].builder == "house"
    assert match.normalize("Glass-fronted Cabinets!") == ["glass", "fronted", "cabinet"]


def test_not_for_hit_lowers_confidence_into_ask_band():
    m, v = top("19th century cup cabinet")
    assert (m.builder, round(m.confidence, 2), v) == ("cabinet", 0.6, "ask")
    assert any("cup cabinet" in r for r in m.reasons)


def test_no_fit_declines():
    m, v = top("phonebooth modern day london")
    assert m.confidence == 0.0 and v == "decline"


def test_two_hits_floor_at_zero():
    ms = match.match_all("cup cabinet locker sideboard", V)
    assert [m for m in ms if m.builder == "cabinet"][0].confidence == pytest.approx(0.2)


def test_tie_between_builders_asks():
    both = {"a": vocab(["thing"]), "b": vocab(["thing"])}
    ms = match.match_all("thing", both)
    assert match.verdict(ms)[0] == "ask"


def test_thresholds_are_the_agreed_ones():
    assert (match.BUILD, match.ASK, match.TIE) == (0.8, 0.5, 0.1)


def test_real_builders_cup_cabinet_asks():
    m, v = top("19th century cup cabinet", vocabs=match.registered_vocabs())
    assert (m.builder, v) == ("cabinet", "ask")


def test_real_builders_sideboard_and_cottage_build():
    r = match.registered_vocabs()
    assert top("scandinavian sideboard", r)[1:] == ("build",)
    assert top("small cottage", r)[0].builder == "house"


def test_cli_match_prints_verdict_and_exits_0(capsys):
    assert cli.main(["match", "spaceship"]) == 0
    assert "verdict: decline" in capsys.readouterr().out


def test_cli_match_empty_request_exits_2(capsys):
    assert cli.main(["match", " "]) == 2


def test_every_makes_phrase_matches_only_its_own_builder_at_build():
    r = match.registered_vocabs()
    for name, v in r.items():
        for phrase in v.makes:
            ms = match.match_all(phrase, r)
            kind, best = match.verdict(ms)
            assert (best.builder if best else None, kind) == (name, "build"), \
                "%r should build with %s, got %s" % (phrase, name, [(m.builder, m.confidence) for m in ms[:2]])
