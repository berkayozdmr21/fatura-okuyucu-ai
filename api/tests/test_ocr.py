import io

import pytest

from app.extraction import extract_document, ocr
from eval.generate import generate

pytestmark = pytest.mark.skipif(not ocr.ocr_available(), reason="rapidocr-onnxruntime kurulu değil")


def test_ocr_images_never_fail_silently():
    """Yanlış okunan bir fotoğraf asla 'temiz' görünmemeli: ya doğru okunur ya da incelemeye düşer."""
    import pypdfium2 as pdfium

    fields = ["seller_vkn", "invoice_no", "invoice_date", "total", "vat_amount"]
    checked = 0
    for c in generate(n=16, seed=5):
        if c.kind != "clean" or c.mime != "application/pdf":
            continue
        buf = io.BytesIO()
        pdfium.PdfDocument(c.content)[0].render(scale=2).to_pil().save(buf, format="PNG")
        res = extract_document(buf.getvalue(), "foto.png", "image/png")
        assert res.extractor == "ocr"
        correct = all(
            res.data[f] is not None and (abs(float(res.data[f]) - float(c.truth[f])) < 0.005
                                         if isinstance(c.truth[f], float) else res.data[f] == c.truth[f])
            for f in fields
        )
        assert correct or res.needs_review, f"sessiz hata: {c.name}"
        checked += 1
    assert checked >= 5


def test_scanned_pdf_goes_through_ocr():
    import pypdfium2 as pdfium
    from PIL import Image

    case = next(c for c in generate(n=8, seed=5) if c.kind == "clean" and c.mime == "application/pdf")
    img = pdfium.PdfDocument(case.content)[0].render(scale=2).to_pil().convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PDF")            # yalnızca görüntü içeren (taranmış) PDF
    res = extract_document(buf.getvalue(), "tarama.pdf", "application/pdf")
    assert res.extractor == "ocr"
    assert res.data["invoice_no"] == case.truth["invoice_no"] or res.needs_review
