import json
from pathlib import Path

import pytest

from chatbot.engine import Engine
from chatbot.llm import validate_output

DIR = Path(__file__).parent


def _load(name):
    return json.loads((DIR / f"heldout_{name}.json").read_text(encoding="utf-8"))


def test_heldout_c_wrong_confident_answers_stay_rare():
    """Yerel mod bilmediğini söylemeli, yanlış cevap vermemeli. C seti motor ayarlanırken hiç kullanılmadı.

    Doğru cevap oranı bilinçli olarak sınanmıyor (kelime tabanlı arama farklı ağızlarda zayıf, README'ye bak);
    ama yanlış bir konuyu kendinden emin cevaplama oranı düşük kalmalı.
    """
    eng = Engine()
    wrong = 0
    rows = _load("c")
    for r in rows:
        out = eng.answer(r["m"], role=r["role"], client=r["client"])
        got = out["matched"] if out["source"] in ("kb", "restricted") else None
        if got is not None and got != r["exp"]:
            wrong += 1
    assert wrong / len(rows) <= 0.12, f"{wrong}/{len(rows)} yanlış cevap"


def test_heldout_a_dev_set_stays_good():
    eng = Engine()
    rows = _load("a")
    ok = sum(
        (eng.answer(r["m"], r["role"], r["client"])["matched"] if
         eng.answer(r["m"], r["role"], r["client"])["source"] in ("kb", "restricted") else None) == r["exp"]
        for r in rows)
    assert ok / len(rows) >= 0.85


# ---------- LLM yolu (sahte istemciyle) ----------

class FakeLLM:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def answer(self, **kw):
        self.calls.append(kw)
        return self.result


def test_llm_is_only_asked_when_local_match_is_not_confident():
    llm = FakeLLM({"answer": "LLM cevabı", "steps": [], "screen": "upload", "matched": "upload"})
    eng = Engine(llm=llm)
    out = eng.answer("Faturayı nasıl yüklerim?", "client", "web")          # güvenli yerel eşleşme
    assert out["source"] == "kb" and llm.calls == []
    out = eng.answer("çektiğim fiş görüntüsünü sisteme nasıl veririm", "client", "mobile")
    assert out["source"] == "llm" and out["answer"] == "LLM cevabı" and len(llm.calls) == 1
    assert out["action"]["screen"] == "upload"


def test_llm_never_receives_more_than_candidates_and_no_documents():
    llm = FakeLLM(None)
    eng = Engine(llm=llm)
    eng.answer("belgemdeki toplam tutar 1.234,56 TL yanlış", "accountant", "web")
    for call in llm.calls:
        assert set(call) == {"message", "role", "client", "candidates", "screens"}
        assert len(call["candidates"]) <= 5


def test_llm_failure_falls_back_to_local_answer():
    eng = Engine(llm=FakeLLM(None))
    out = eng.answer("unuttuğum parolayı e-postama yollar mısınız", "client", "web")
    assert out["source"] in ("fallback", "kb")


def test_llm_screen_is_checked_against_client_availability():
    llm = FakeLLM({"answer": "İnceleme ekranına git", "steps": [], "screen": "review", "matched": "review"})
    eng = Engine(llm=llm)
    out = eng.answer("şüpheli çıkan evrakları tek tek açıp bakmak istiyorum", "accountant", "mobile")
    assert out["source"] == "llm" and out["action"] is None      # mobilde "review" ekranı yok


def test_validate_output_rejects_bad_shapes_and_unknown_screens():
    screens = {"upload": {}, "documents": {}}
    assert validate_output(None, screens, ["a"]) is None
    assert validate_output({"answer": ""}, screens, ["a"]) is None
    assert validate_output({"answer": 5}, screens, ["a"]) is None
    ok = validate_output({"answer": " Tamam ", "steps": ["x", 3, "", "y"], "screen": "evil", "matched": "zzz"},
                         screens, ["a"])
    assert ok == {"answer": "Tamam", "steps": ["x", "y"], "screen": None, "matched": None}
    assert validate_output({"answer": "a" * 5000}, screens, [])["answer"].__len__() == 900
    assert validate_output({"answer": "x", "screen": "upload", "matched": "a"}, screens, ["a"])["screen"] == "upload"
