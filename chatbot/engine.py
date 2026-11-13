"""Yardım asistanı motoru: bilgi tabanında arama, rol/istemci kuralları, yönlendirme eylemi.

Önce kural/arama tabanlı çalışır (hızlı, ücretsiz, veri dışarı çıkmaz). İsteğe bağlı olarak belirsiz
sorularda Claude devreye girer (bkz. llm.py); Claude yalnızca bilgi tabanındaki içeriğe dayanarak yanıt verir.
"""
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .text import STOPWORDS, fold, stems, tokens

KB_PATH = Path(__file__).with_name("knowledge.json")

MIN_MATCH = 0.55          # bunun altı "anlayamadım"
CONFIDENT = 0.85          # bunun üstünde LLM'e gerek yok
AMBIGUITY_MARGIN = 0.05   # ilk iki aday arasındaki fark bundan küçükse kullanıcıya sor
UNKNOWN_PENALTY = 0.4     # bilgi tabanında geçmeyen sözcüğün paydadaki ağırlığı (1.0 = tam ceza)

_WHERE = re.compile(r"\b(nerede|nereden|nereye|nerde|neresi|bulam\w*|goremi\w*|gozukmuyor|goremedim|hangi (sekme|menu|sayfa|ekran|bolum))\b")
_GREETING = re.compile(r"^\s*(merhaba|selam|selamlar|gunaydin|iyi gunler|iyi aksamlar|hey|naber|slm)\b")
_THANKS = re.compile(r"\b(tesekkur\w*|sagol\w*|eyvallah|saol|tskler|tsk)\b")
_HUMAN = re.compile(r"\b(insan|canli destek|temsilci|yetkili)\b")

SCREEN_TOPIC = {"upload": "upload", "documents": "documents", "review": "review", "export": "export", "team": "invite"}


@dataclass
class Entry:
    id: str
    title: str
    screen: Optional[str]
    roles: List[str]
    clients: List[str]
    keywords: List[str]
    examples: List[str]
    answer: str
    steps: List[str]
    available: bool = True
    weights: Dict[str, float] = field(default_factory=dict)
    phrases: List[str] = field(default_factory=list)
    tokens: set = field(default_factory=set)       # kökü değil, tam (katlanmış) sözcükler


class Engine:
    def __init__(self, kb: Optional[dict] = None, kb_path: Optional[Path] = None, llm: Any = None):
        data = kb if kb is not None else json.loads(Path(kb_path or KB_PATH).read_text(encoding="utf-8"))
        self.screens: Dict[str, dict] = data["screens"]
        self.small: Dict[str, str] = data["smalltalk"]
        self.entries: List[Entry] = [Entry(
            id=e["id"], title=e["title"], screen=e.get("screen"), roles=e["roles"], clients=e["clients"],
            keywords=e["keywords"], examples=e["examples"], answer=e["answer"], steps=e.get("steps", []),
            available=e.get("available", True)) for e in data["entries"]]
        self.by_id = {e.id: e for e in self.entries}
        self.llm = llm
        self._index()

    # ---------- indeks ----------
    def _index(self) -> None:
        df: Dict[str, int] = {}
        for e in self.entries:
            w: Dict[str, float] = {}
            for s in stems(e.title):
                w[s] = max(w.get(s, 0), 0.8)
            for ex in e.examples:
                for s in stems(ex):
                    w[s] = max(w.get(s, 0), 0.8)
            for kw in e.keywords:
                for s in stems(kw):
                    w[s] = 1.0
                if " " in kw.strip():
                    e.phrases.append(fold(kw).strip())
            e.weights = w
            e.tokens = {t for text in [e.title, *e.keywords, *e.examples] for t in tokens(text) if t not in STOPWORDS}
            for s in w:
                df[s] = df.get(s, 0) + 1
        n = len(self.entries)
        self.idf = {s: math.log((n + 1) / (c + 1)) + 1 for s, c in df.items()}
        self.unknown_idf = math.log((n + 1) / 1) + 1

    # ---------- puanlama ----------
    def _score(self, query_stems: List[str], folded: str, e: Entry) -> float:
        qset = set(query_stems)
        if not qset:
            return 0.0
        # Günlük konuşmadaki bilinmeyen sözcükler ("kaybettim", "acaba") skoru tamamen çökertmesin
        known = sum(self.idf[s] for s in qset if s in self.idf)
        unknown = sum(self.unknown_idf for s in qset if s not in self.idf)
        hit = sum(self.idf[s] * e.weights[s] for s in qset if s in e.weights)
        score = hit / (known + UNKNOWN_PENALTY * unknown) if known else 0.0
        # Kök eşleşmesi aynı kalan yakın sözcükleri (incelemede / inceleme) ayırmak için tam sözcük eşleşmesi
        q_tokens = {t for t in tokens(folded) if t not in STOPWORDS}
        if q_tokens:
            score += 0.15 * len(q_tokens & e.tokens) / len(q_tokens)
        if any(re.search(r"\b" + re.escape(p) + r"\b", folded) for p in e.phrases):
            score += 0.25
        return score

    def rank(self, message: str) -> List[tuple]:
        folded = fold(message)
        q = stems(message)
        scored = [(self._score(q, folded, e), e) for e in self.entries]
        return sorted(scored, key=lambda x: -x[0])

    # ---------- yardımcılar ----------
    def _where_text(self, screen: str, client: str) -> str:
        label = self.screens[screen]["label"]
        return f"Alt menüdeki “{label}” sekmesi" if client == "mobile" else f"Sol menüdeki “{label}” bölümü"

    def _action(self, screen: Optional[str], client: str) -> Optional[dict]:
        if not screen or screen not in self.screens or client not in self.screens[screen]["clients"]:
            return None
        return {"type": "navigate", "screen": screen, "label": f"“{self.screens[screen]['label']}” ekranını aç"}

    def _resp(self, answer: str, source: str, *, steps=None, action=None, suggestions=None, matched=None,
              confidence: float = 0.0, where: Optional[str] = None) -> dict:
        return {"answer": answer, "steps": steps or [], "action": action, "suggestions": suggestions or [],
                "matched": matched, "confidence": round(min(confidence, 1.0), 2), "source": source, "where": where}

    def topics(self, role: str, client: str) -> List[str]:
        """Arayüzde hızlı soru düğmeleri olarak gösterilecek örnek sorular."""
        usable = [e for e in self.entries if e.available and role in e.roles and client in e.clients and e.examples]
        # Role özel olan konular (ör. muhasebeci: inceleme, dışa aktarma) öne alınır
        usable.sort(key=lambda e: 0 if len(e.roles) == 1 else 1)
        return [e.examples[0] for e in usable][:8]

    def _suggestions(self, ranked, skip_id: Optional[str], role: str, client: str, n: int = 3) -> List[str]:
        out = []
        for score, e in ranked:
            if e.id == skip_id or score < 0.3 or role not in e.roles or client not in e.clients or not e.available:
                continue
            out.append(e.examples[0])
            if len(out) == n:
                break
        return out

    # ---------- ana akış ----------
    def answer(self, message: str, role: str = "client", client: str = "web", screen: Optional[str] = None) -> dict:
        folded = fold(message)

        if _GREETING.search(folded) and len(folded.split()) <= 4:
            return self._resp(self.small["greeting"], "smalltalk", suggestions=self.topics(role, client)[:4])
        if _THANKS.search(folded) and len(folded.split()) <= 5:
            return self._resp(self.small["thanks"], "smalltalk")

        ranked = self.rank(message)
        best_score, best = ranked[0]
        second_score = ranked[1][0] if len(ranked) > 1 else 0.0

        # Ekran bağlamı: kısa/genel soru ("bunu nasıl yaparım") bulunulan ekrana göre yanıtlanır
        if best_score < MIN_MATCH and screen in SCREEN_TOPIC and len(folded.split()) <= 5:
            best, best_score = self.by_id[SCREEN_TOPIC[screen]], MIN_MATCH

        if _HUMAN.search(folded) and best_score < CONFIDENT:
            best, best_score = self.by_id["support"], 1.0

        ambiguous = (best_score >= MIN_MATCH and best_score - second_score < AMBIGUITY_MARGIN
                     and ranked[1][1].id != best.id and best is ranked[0][1])
        confident = best_score >= CONFIDENT and not ambiguous

        # Belirsiz veya zayıf sorularda (varsa) LLM'den yardım iste
        if self.llm is not None and not confident and not _HUMAN.search(folded):
            out = self._ask_llm(message, role, client, ranked)
            if out is not None:
                return out

        if best_score < MIN_MATCH:
            sug = self._suggestions(ranked, None, role, client)
            if sug:
                return self._resp(self.small["fallback"], "fallback", suggestions=sug)
            return self._resp(self.small["off_topic"], "fallback", suggestions=self.topics(role, client)[:4])

        if ambiguous:
            sug = self._suggestions(ranked, None, role, client, n=3)
            return self._resp(self.small["fallback"], "fallback", suggestions=sug, matched=best.id,
                              confidence=best_score)

        return self._compose(best, best_score, folded, role, client, ranked)

    def _compose(self, e: Entry, score: float, folded: str, role: str, client: str, ranked) -> dict:
        if role not in e.roles:
            who = "muhasebeci" if "accountant" in e.roles else "müşteri"
            text = (f"“{e.title}” yalnızca {who} hesabında kullanılabilir. "
                    "Kendi belgelerini “Belgeler” ekranında görebilir, yeni belge yükleyebilirsin; "
                    "bu işlem için bürondaki muhasebeciyle iletişime geçebilirsin.")
            return self._resp(text, "restricted", action=self._action("documents", client), matched=e.id,
                              confidence=score, suggestions=self._suggestions(ranked, e.id, role, client))
        if client not in e.clients:
            others = " veya ".join({"web": "web", "desktop": "masaüstü"}[c] for c in e.clients if c in ("web", "desktop"))
            text = (f"“{e.title}” {client == 'mobile' and 'mobil uygulamada' or 'bu uygulamada'} yok; "
                    f"{others or 'web'} uygulamasından kullanabilirsin.")
            return self._resp(text, "restricted", matched=e.id, confidence=score,
                              suggestions=self._suggestions(ranked, e.id, role, client))

        action = self._action(e.screen, client)
        where = self._where_text(e.screen, client) if action else None
        text = e.answer
        if where and _WHERE.search(folded):
            text = f"{where} içinde bulabilirsin. " + text
        return self._resp(text, "kb", steps=e.steps, action=action, matched=e.id, confidence=score, where=where,
                          suggestions=self._suggestions(ranked, e.id, role, client))

    def _ask_llm(self, message: str, role: str, client: str, ranked) -> Optional[dict]:
        candidates = [e for s, e in ranked[:5] if s > 0.15] or [ranked[0][1]]
        out = self.llm.answer(message=message, role=role, client=client, candidates=candidates, screens=self.screens)
        if out is None:
            return None
        screen = out.get("screen")
        return self._resp(out["answer"], "llm", steps=out.get("steps"), action=self._action(screen, client),
                          matched=out.get("matched"), confidence=0.0,
                          where=self._where_text(screen, client) if self._action(screen, client) else None,
                          suggestions=self._suggestions(ranked, out.get("matched"), role, client))
