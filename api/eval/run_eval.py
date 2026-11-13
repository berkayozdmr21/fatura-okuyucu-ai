"""Çıkarım hattının doğruluğunu ölçer ve Markdown rapor yazar.

Kullanım (api/ klasöründen):
    python -m eval.run_eval --n 200 --seed 11 --out eval/REPORT.md

DİKKAT: Test seti sentetiktir (eval/generate.py). Buradaki yüzdeler gerçek dünya doğruluğu değildir;
gerçek, anonimleştirilmiş belgelerle ayrıca ölçülmelidir.
"""
import argparse
import time
from collections import Counter, defaultdict
from pathlib import Path

from app.extraction import extract_document
from app.extraction.schema import FIELDS

from .generate import generate

NUMERIC = {"subtotal", "vat_amount", "total"}


def _equal(field: str, got, want) -> bool:
    if want is None:
        return got is None
    if got is None:
        return False
    if field in NUMERIC:
        return abs(float(got) - float(want)) < 0.005
    if field == "vat_rate":
        return int(got) == int(want)
    return str(got).strip().lower() == str(want).strip().lower()


def run(n: int, seed: int):
    cases = generate(n=n, seed=seed)
    field_ok = defaultdict(int)
    field_total = defaultdict(int)
    per_template = defaultdict(lambda: [0, 0])      # [tam doğru belge, toplam]
    bad_total = bad_flagged = clean_total = clean_flagged = 0
    extractors = Counter()
    t0 = time.perf_counter()

    for c in cases:
        res = extract_document(c.content, c.name, c.mime)
        extractors[res.extractor] += 1
        if c.kind == "clean":
            clean_total += 1
            clean_flagged += int(res.needs_review)
            all_ok = True
            for f in FIELDS:
                if c.truth.get(f) is None and f not in ("buyer_name", "buyer_vkn"):
                    continue
                ok = _equal(f, res.data.get(f), c.truth.get(f))
                field_total[f] += 1
                field_ok[f] += int(ok)
                all_ok &= ok
            per_template[c.template][0] += int(all_ok)
            per_template[c.template][1] += 1
        else:
            bad_total += 1
            bad_flagged += int(res.needs_review)

    elapsed = time.perf_counter() - t0
    return {
        "n": len(cases), "seconds": elapsed, "field_ok": field_ok, "field_total": field_total,
        "per_template": per_template, "bad_total": bad_total, "bad_flagged": bad_flagged,
        "clean_total": clean_total, "clean_flagged": clean_flagged, "extractors": extractors,
    }


def report(r: dict, seed: int) -> str:
    out = ["# Doğruluk raporu (sentetik veri)", "",
           "> Bu sonuçlar **sentetik** faturalarla ölçüldü (`eval/generate.py`). Şablonlar çözümleyiciyi yazarken "
           "bilinen biçimlerdir; gerçek dünya doğruluğu bunun altında olacaktır. Gerçek, anonimleştirilmiş belgelerle "
           "ayrıca ölçülmelidir.", "",
           f"- Belge sayısı: **{r['n']}** (seed={seed}), toplam süre: {r['seconds']:.2f} sn "
           f"({1000 * r['seconds'] / max(r['n'], 1):.1f} ms/belge)",
           f"- Çıkarıcılar: {dict(r['extractors'])}", "",
           "## Alan bazında doğruluk (hatasız belgelerde)", "", "| Alan | Doğru / Toplam | Doğruluk |", "|---|---|---|"]
    for f in FIELDS:
        t = r["field_total"].get(f, 0)
        if t:
            ok = r["field_ok"][f]
            out.append(f"| `{f}` | {ok} / {t} | %{100 * ok / t:.1f} |")
    out += ["", "## Şablon bazında tam doğru belge oranı", "", "| Şablon | Tam doğru | Oran |", "|---|---|---|"]
    names = {"A": "A: etiket:değer aynı satır (e-Arşiv)", "B": "B: etiket ve değer ayrı satır",
             "C": "C: perakende fişi", "X": "X: UBL-TR XML"}
    for k in sorted(r["per_template"]):
        ok, t = r["per_template"][k]
        out.append(f"| {names.get(k, k)} | {ok} / {t} | %{100 * ok / t:.1f} |")
    out += ["", "## Hata yakalama (doğrulama kuralları)", "",
            f"- Bilinçli bozulmuş belgeler (yanlış VKN veya toplam): **{r['bad_flagged']} / {r['bad_total']}** "
            f"incelemeye işaretlendi (%{100 * r['bad_flagged'] / max(r['bad_total'], 1):.1f})",
            f"- Temiz belgelerde gereksiz inceleme (yanlış alarm): **{r['clean_flagged']} / {r['clean_total']}** "
            f"(%{100 * r['clean_flagged'] / max(r['clean_total'], 1):.1f})", ""]
    return "\n".join(out)


def run_ocr(n: int, seed: int) -> str:
    """PDF'leri görüntüye çevirip yerel OCR hattından geçirir (rapidocr-onnxruntime gerekir).

    Görüntüler temiz render edilmiştir (kamera gürültüsü, eğiklik, gölge yok); gerçek fotoğraflarda sonuç düşer.
    Asıl ölçülen şey: yanlış okunan belgelerin sessizce geçmeyip incelemeye düşmesi.
    """
    import io

    import pypdfium2 as pdfium

    from app.extraction import ocr

    if not ocr.ocr_available():
        return "\n## OCR hattı\n\nYerel OCR kurulu değil (`pip install rapidocr-onnxruntime`), ölçülmedi.\n"
    fields = ["seller_vkn", "invoice_no", "invoice_date", "total", "vat_amount", "vat_rate", "subtotal"]
    total = exact = flagged = silent = 0
    for c in generate(n=n, seed=seed):
        if c.kind != "clean" or c.mime != "application/pdf":
            continue
        buf = io.BytesIO()
        pdfium.PdfDocument(c.content)[0].render(scale=2).to_pil().save(buf, format="PNG")
        res = extract_document(buf.getvalue(), "foto.png", "image/png")
        all_ok = all(_equal(f, res.data.get(f), c.truth.get(f)) for f in fields)
        total += 1
        exact += int(all_ok)
        flagged += int(res.needs_review)
        silent += int((not all_ok) and not res.needs_review)
    return (
        "\n## OCR hattı (PDF -> görüntü -> yerel OCR)\n\n"
        "> Temiz render edilmiş görüntüler; gerçek telefon fotoğraflarında (eğiklik, gölge, buruşuk fiş) sonuç düşer.\n\n"
        f"- Belge: **{total}**, tüm alanları doğru: **{exact}** (%{100 * exact / max(total, 1):.1f})\n"
        f"- İncelemeye işaretlenen: **{flagged}**\n"
        f"- **Sessiz hata** (yanlış okundu ama işaretlenmedi): **{silent}**\n"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out", default="eval/REPORT.md")
    ap.add_argument("--ocr", action="store_true", help="OCR hattını da ölç (yavaş)")
    args = ap.parse_args()
    result = run(args.n, args.seed)
    text = report(result, args.seed)
    if args.ocr:
        text += run_ocr(min(args.n, 120), args.seed)
    Path(args.out).write_text(text, encoding="utf-8")
    print(text)
