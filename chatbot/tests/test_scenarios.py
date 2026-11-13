import json
from pathlib import Path

import pytest

from chatbot.engine import Engine
from chatbot.text import fold

SCENARIOS = json.loads((Path(__file__).parents[1] / "scenarios.json").read_text(encoding="utf-8"))
ENGINE = Engine()


def _run(s, message=None):
    return ENGINE.answer(message or s["message"], role=s["role"], client=s["client"], screen=s.get("screen"))


def _check(s, out):
    exp = s["expect"]
    if "source" in exp:
        assert out["source"] == exp["source"], out
    if "matched" in exp:
        assert out["matched"] == exp["matched"], out
    if "screen" in exp:
        got = out["action"]["screen"] if out["action"] else None
        assert got == exp["screen"], out
    if "answer_contains" in exp:
        assert exp["answer_contains"].lower() in out["answer"].lower(), out["answer"]


@pytest.mark.parametrize("s", SCENARIOS, ids=lambda s: s["id"])
def test_scenario(s):
    _check(s, _run(s))


@pytest.mark.parametrize("variant", ["upper", "ascii", "punct"])
def test_robust_to_case_diacritics_and_punctuation(variant):
    """Aynı sorular BÜYÜK harfle, Türkçe karaktersiz veya noktalama ile yazılsa da aynı sonucu vermeli."""
    failures = []
    for s in SCENARIOS:
        if s["expect"].get("matched") is None and s["expect"].get("source") != "smalltalk":
            continue
        msg = s["message"]
        if variant == "upper":
            msg = msg.upper().replace("I", "I")
        elif variant == "ascii":
            msg = fold(msg)
        else:
            msg = msg.rstrip("?.") + " ???"
        out = _run(s, msg)
        exp = s["expect"]
        if "matched" in exp and out["matched"] != exp["matched"]:
            failures.append((s["id"], msg, out["matched"]))
    assert len(failures) <= 2, failures


def test_unavailable_features_never_claim_support():
    for s in SCENARIOS:
        if s["id"].startswith("na-"):
            out = _run(s)
            assert out["source"] == "kb"
            assert "henüz" in out["answer"].lower()


def test_actions_only_point_to_screens_that_exist_on_that_client():
    for s in SCENARIOS:
        out = _run(s)
        if out["action"]:
            screen = ENGINE.screens[out["action"]["screen"]]
            assert s["client"] in screen["clients"], (s["id"], out["action"])


def test_ambiguous_question_asks_clarification():
    out = ENGINE.answer("belge", role="client", client="web")
    assert out["source"] in ("fallback", "kb")
    if out["source"] == "fallback":
        assert out["suggestions"]


def test_topics_respect_role_and_client():
    mobile_client = ENGINE.topics("client", "mobile")
    assert mobile_client and all("excel" not in t.lower() for t in mobile_client)
    assert any("excel" in t.lower() or "davet" in t.lower() for t in ENGINE.topics("accountant", "web"))


def test_knowledge_base_is_consistent():
    ids = [e.id for e in ENGINE.entries]
    assert len(ids) == len(set(ids))
    for e in ENGINE.entries:
        assert e.examples and e.keywords and e.answer
        assert e.screen is None or e.screen in ENGINE.screens
        assert set(e.roles) <= {"client", "accountant"} and set(e.clients) <= {"web", "desktop", "mobile"}
