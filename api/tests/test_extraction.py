import pytest
from fpdf import FPDF

from app.extraction import extract_document
from eval.generate import generate

CASES = generate(n=80, seed=5)
CLEAN = [c for c in CASES if c.kind == "clean"]
BAD = [c for c in CASES if c.kind != "clean"]


@pytest.mark.parametrize("case", CLEAN, ids=lambda c: c.name)
def test_clean_documents_extract_exactly(case):
    res = extract_document(case.content, case.name, case.mime)
    assert not res.failed
    for field in ("seller_vkn", "invoice_no", "invoice_date", "total", "vat_amount", "subtotal", "vat_rate"):
        want = case.truth[field]
        got = res.data[field]
        if isinstance(want, float):
            assert got == pytest.approx(want, abs=0.005), field
        else:
            assert got == want, field
    assert res.needs_review is False, res.issues


@pytest.mark.parametrize("case", BAD, ids=lambda c: c.name)
def test_corrupted_documents_are_flagged(case):
    res = extract_document(case.content, case.name, case.mime)
    assert res.needs_review, f"{case.kind} yakalanmadı"


def test_ubl_xml_buyer_and_seller():
    case = next(c for c in CLEAN if c.template == "X")
    res = extract_document(case.content, case.name, case.mime)
    assert res.extractor == "ubl_xml"
    assert res.data["buyer_vkn"] == case.truth["buyer_vkn"]
    assert res.data["seller_name"] == case.truth["seller_name"]


def test_xml_with_doctype_is_rejected():
    evil = b'<?xml version="1.0"?><!DOCTYPE a [<!ENTITY x "y">]><Invoice/>'
    res = extract_document(evil, "x.xml", "application/xml")
    assert res.failed and res.needs_review


def test_garbage_xml_fails_gracefully():
    res = extract_document(b"<not-an-invoice/>", "x.xml", "application/xml")
    assert res.failed


def test_blank_scanned_pdf_is_never_marked_clean():
    pdf = FPDF()
    pdf.add_page()
    res = extract_document(bytes(pdf.output()), "scan.pdf", "application/pdf")
    assert res.needs_review                      # boş belge asla "temiz" görünmemeli
    if res.failed:                               # OCR kurulu değilse nedeni açıkça söylenir
        assert res.issues[0]["code"] == "ocr_unavailable"
    else:                                        # OCR kuruluysa zorunlu alanlar okunamadı diye işaretlenir
        assert res.extractor == "ocr"
        assert any(i["code"] == "missing_field" for i in res.issues)


def test_corrupt_pdf_fails_gracefully():
    res = extract_document(b"%PDF-1.4 not really a pdf", "x.pdf", "application/pdf")
    assert res.failed


def test_unsupported_type():
    res = extract_document(b"hello", "x.txt", "text/plain")
    assert res.failed and res.issues[0]["code"] == "unsupported_type"
