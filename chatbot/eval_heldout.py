"""Hiç ayarlanmamış (held-out) sorularla yerel motorun doğruluğunu ölçer.

    python -m chatbot.eval_heldout            (depo kökünden)

A seti geliştirme sırasında hatalarından ders çıkarılan setti. B seti de sonradan bilgi tabanı genişletilirken
dolaylı olarak sızdı (B'yi yazdıktan sonra anahtar kelime eklendi), yani tarafsız DEĞİLDİR. C seti anahtar
kelimeler eklendikten sonra yazıldı ve tek seferlik ölçüm içindir; gerçek başarıyı yalnızca C gösterir.
"exp": null olan sorular konu dışıdır; doğru davranış eşleşme VERMEMEKTİR.
"""
import json
import sys
from pathlib import Path

from .engine import Engine

DIR = Path(__file__).parent / "tests"


def evaluate(name: str, engine: Engine, verbose: bool = False) -> float:
    rows = json.loads((DIR / f"heldout_{name}.json").read_text(encoding="utf-8"))
    ok = 0
    for r in rows:
        out = engine.answer(r["m"], role=r["role"], client=r["client"])
        got = out["matched"] if out["source"] in ("kb", "restricted") else None
        good = got == r["exp"]
        ok += good
        if verbose and not good:
            print(f"  X [{name}] {r['m']!r}: beklenen={r['exp']} gelen={got} ({out['source']})")
    acc = ok / len(rows)
    print(f"{name.upper()} seti: {ok}/{len(rows)} (%{100 * acc:.0f})")
    return acc


if __name__ == "__main__":
    eng = Engine()
    for n in ("a", "b", "c"):
        evaluate(n, eng, verbose="-v" in sys.argv)
