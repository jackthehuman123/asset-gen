import itertools

import pytest

from rbxasset.builders import REGISTRY, load_vocab


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_builder_declares_scope(name):
    v = load_vocab(name)
    assert v.makes and v.not_for, "%s must fill in makes and not_for" % name
    for phrase in v.makes + v.not_for:
        assert phrase == phrase.strip().lower() and phrase, (name, phrase)
    assert not set(v.makes) & set(v.not_for), "%s lists the same phrase in both" % name


def test_builders_do_not_claim_the_same_thing():
    for a, b in itertools.combinations(sorted(REGISTRY), 2):
        both = set(load_vocab(a).makes) & set(load_vocab(b).makes)
        assert not both, "%s and %s both claim %s" % (a, b, sorted(both))
