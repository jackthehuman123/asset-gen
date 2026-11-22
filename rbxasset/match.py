"""Builder matching: how well does a request fit each registered builder? bpy-free.

Score per builder = 1.0 if a `makes` phrase appears in the request (else 0.0; a longer phrase
matched by another builder shadows a shorter one it contains),
minus 0.4 for each `not_for` phrase that also appears; clamped to 0..1.
Verdict: build >= BUILD; ask for ASK <= score < BUILD or when two builders at
>= ASK are within TIE of each other; decline below ASK.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from rbxasset.builders import REGISTRY, load_vocab
from rbxasset.builders.vocab import Vocab

BUILD = 0.8
ASK = 0.5
TIE = 0.1
PENALTY = 0.4


@dataclass
class Match:
    builder: str
    confidence: float
    reasons: List[str] = field(default_factory=list)


def _stem(w: str) -> str:
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    return w


def normalize(text: str) -> List[str]:
    return [_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower())]


def _contains(tokens: List[str], phrase: List[str]) -> bool:
    n = len(phrase)
    return n > 0 and any(tokens[i:i + n] == phrase for i in range(len(tokens) - n + 1))


def registered_vocabs() -> Dict[str, Vocab]:
    return {name: load_vocab(name) for name in REGISTRY}


def match_all(request: str, vocabs: Optional[Dict[str, Vocab]] = None) -> List[Match]:
    vocabs = vocabs if vocabs is not None else registered_vocabs()
    tokens = normalize(request)
    found = {name: [p for p in v.makes if _contains(tokens, normalize(p))] for name, v in vocabs.items()}
    out = []
    for name, v in vocabs.items():
        # a longer phrase matched by another builder shadows a shorter one it contains
        # ("japanese farmhouse" beats "farmhouse")
        live, reasons = [], []
        for p in found[name]:
            pt = normalize(p)
            shadow = next((q for other, qs in found.items() if other != name for q in qs
                           if len(normalize(q)) > len(pt) and _contains(normalize(q), pt)), None)
            if shadow:
                reasons.append("'%s' is shadowed by '%s'" % (p, shadow))
            else:
                live.append(p)
        hits = [p for p in v.not_for if _contains(tokens, normalize(p))]
        reasons = ["makes '%s'" % p for p in live] + reasons + ["not for '%s'" % p for p in hits]
        conf = 0.0 if not live else max(0.0, min(1.0, 1.0 - PENALTY * len(hits)))
        out.append(Match(name, round(conf, 6), reasons))
    return sorted(out, key=lambda m: (-m.confidence, m.builder))


def verdict(matches: List[Match]) -> Tuple[str, Optional[Match]]:
    if not matches or matches[0].confidence < ASK:
        return "decline", None
    best = matches[0]
    if len(matches) > 1 and matches[1].confidence >= ASK \
            and round(best.confidence - matches[1].confidence, 6) <= TIE:
        return "ask", best
    return ("build" if best.confidence >= BUILD else "ask"), best
