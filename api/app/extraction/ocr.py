"""İsteğe bağlı yerel OCR. `rapidocr-onnxruntime` kuruluysa taranmış PDF ve fotoğraflar okunur.

Kurulu değilse `ocr_available()` False döner ve çağıran taraf (pipeline) uygun uyarıyı üretir.
Veri hiçbir yere gönderilmez.
"""
import io
from typing import Optional

_engine = None
_checked = False


def _get_engine():
    global _engine, _checked
    if not _checked:
        _checked = True
        try:
            from rapidocr_onnxruntime import RapidOCR  # type: ignore

            _engine = RapidOCR()
        except Exception:  # paket yok ya da başlatılamadı
            _engine = None
    return _engine


def ocr_available() -> bool:
    return _get_engine() is not None


def image_to_text(image_bytes: bytes) -> Optional[str]:
    """Görüntüden metin satırlarını (yukarıdan aşağı) döndürür. OCR yoksa None."""
    engine = _get_engine()
    if engine is None:
        return None
    import numpy as np
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    result, _ = engine(np.array(img))
    if not result:
        return ""
    # result: [[kutu, metin, güven], ...]; aynı satırdaki parçaları birleştir
    items = sorted(result, key=lambda r: (round(r[0][0][1] / 12), r[0][0][0]))
    lines, current_key, current = [], None, []
    for box, txt, _score in items:
        key = round(box[0][1] / 12)
        if current_key is not None and key != current_key:
            lines.append(" ".join(current))
            current = []
        current_key = key
        current.append(txt)
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


def pdf_first_pages_to_images(pdf_bytes: bytes, max_pages: int = 2, scale: float = 2.0):
    """Taranmış PDF'in ilk sayfalarını PNG baytlarına çevirir (pypdfium2)."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(pdf_bytes)
    out = []
    for i in range(min(len(pdf), max_pages)):
        pil = pdf[i].render(scale=scale).to_pil()
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        out.append(buf.getvalue())
    return out
