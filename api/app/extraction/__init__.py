"""Belge -> yapılandırılmış fatura verisi hattı.

Sıra: dosya türünü belirle -> (UBL XML | PDF metni | OCR) -> doğrula -> gerekirse isteğe bağlı Claude.
"""
import io
from pathlib import PurePath
from typing import Optional

from ..config import settings
from . import llm, ocr
from .schema import ExtractionResult, empty_data
from .text_parser import parse_text
from .ubl_xml import parse_ubl
from .validators import decide_review, validate

IMAGE_MIMES = {"image/png", "image/jpeg", "image/webp"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
MIN_TEXT_LEN = 30


def _issue(code: str, message: str) -> dict:
    return {"code": code, "field": None, "severity": "error", "message": message}


def _finish(result: ExtractionResult) -> ExtractionResult:
    if not result.failed:
        result.issues.extend(validate(result.data))
    result.needs_review = result.failed or decide_review(result.issues, result.confidence)
    return result


def _pdf_text(content: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    return "\n".join((page.extract_text() or "") for page in reader.pages[:5])


def _local_extract(content: bytes, filename: str, mime: str) -> ExtractionResult:
    ext = PurePath(filename).suffix.lower()
    res = ExtractionResult()

    if ext == ".xml" or mime in ("application/xml", "text/xml"):
        try:
            res.data, res.confidence = parse_ubl(content)
            res.extractor = "ubl_xml"
        except Exception as exc:  # bozuk veya UBL olmayan XML
            res.failed, res.extractor = True, "ubl_xml"
            res.issues.append(_issue("xml_invalid", f"XML okunamadı: {exc}"))
        return res

    text = ""
    if ext == ".pdf" or mime == "application/pdf":
        try:
            text = _pdf_text(content)
        except Exception:
            res.failed, res.extractor = True, "pdf_text"
            res.issues.append(_issue("pdf_unreadable", "PDF dosyası okunamadı veya bozuk."))
            return res
        if len(text.strip()) >= MIN_TEXT_LEN:
            res.extractor = "pdf_text"
        else:  # taranmış PDF: sayfaları görüntüye çevirip OCR dene
            if ocr.ocr_available():
                parts = [ocr.image_to_text(img) or "" for img in ocr.pdf_first_pages_to_images(content)]
                text, res.extractor = "\n".join(parts), "ocr"
            else:
                res.failed = True
                res.issues.append(_issue(
                    "ocr_unavailable",
                    "Taranmış PDF; metin katmanı yok. Yerel OCR kurulu değil (rapidocr-onnxruntime)."))
                return res
    elif ext in IMAGE_EXTS or mime in IMAGE_MIMES:
        if ocr.ocr_available():
            text, res.extractor = ocr.image_to_text(content) or "", "ocr"
        else:
            res.failed = True
            res.issues.append(_issue(
                "ocr_unavailable", "Fotoğraf okumak için yerel OCR kurulu değil (rapidocr-onnxruntime)."))
            return res
    else:
        res.failed = True
        res.issues.append(_issue("unsupported_type", "Desteklenmeyen dosya türü (PDF, XML, PNG, JPG, WEBP)."))
        return res

    res.raw_text = text
    res.data, res.confidence = parse_text(text) if text.strip() else (empty_data(), {})
    if res.extractor == "ocr":  # OCR hataya daha açıktır
        res.confidence = {k: min(v, 0.85) for k, v in res.confidence.items()}
    return res


def _error_count(res: ExtractionResult) -> int:
    return sum(1 for i in res.issues if i["severity"] == "error")


def extract_document(content: bytes, filename: str, mime: str) -> ExtractionResult:
    res = _finish(_local_extract(content, filename, mime))

    wants_llm = (
        settings.extraction_mode == "hybrid"
        and res.extractor != "ubl_xml"
        and (res.failed or res.needs_review)
        and llm.llm_available()
    )
    if wants_llm:
        llm_mime = "application/pdf" if filename.lower().endswith(".pdf") else mime
        out: Optional[tuple] = llm.llm_extract(content, llm_mime)
        if out is not None:
            candidate = ExtractionResult(data=out[0], confidence=out[1], extractor="llm")
            candidate = _finish(candidate)
            if res.failed or _error_count(candidate) < _error_count(res):
                return candidate
    return res
