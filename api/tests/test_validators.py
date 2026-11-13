from datetime import date

from app.extraction.parsing import parse_amount, parse_date
from app.extraction.validators import (check_tax_id, decide_review, effective_confidence, is_valid_tckn,
                                       is_valid_vkn, validate)
from eval.generate import make_vkn
import random


def test_vkn_generated_numbers_are_valid_and_corruption_detected():
    rng = random.Random(1)
    for _ in range(200):
        vkn = make_vkn(rng)
        assert is_valid_vkn(vkn)
        wrong = vkn[:-1] + str((int(vkn[-1]) + 1) % 10)
        assert not is_valid_vkn(wrong)


def test_vkn_rejects_bad_format():
    assert not is_valid_vkn("123")
    assert not is_valid_vkn("abcdefghij")
    assert not is_valid_vkn("")


def test_tckn_known_valid_and_invalid():
    assert is_valid_tckn("10000000146")        # yaygın kullanılan test numarası
    assert not is_valid_tckn("10000000147")
    assert not is_valid_tckn("00000000000")
    assert not is_valid_tckn("1234")


def test_check_tax_id_codes():
    assert check_tax_id(None) is None
    assert check_tax_id("12345") == "tax_id_length"
    assert check_tax_id("10000000146") is None
    assert check_tax_id("10000000147") == "tckn_invalid"


def test_parse_amount_variants():
    assert parse_amount("1.234,56 TL") == 1234.56
    assert parse_amount("₺1.234,56") == 1234.56
    assert parse_amount("1,234.56") == 1234.56
    assert parse_amount("1234,5") == 1234.5
    assert parse_amount("12.500") == 12500.0      # Türkçe binlik ayracı
    assert parse_amount("0,99") == 0.99
    assert parse_amount("abc") is None


def test_parse_date_variants():
    assert parse_date("12.03.2025") == "2025-03-12"
    assert parse_date("12/03/2025") == "2025-03-12"
    assert parse_date("2025-03-12") == "2025-03-12"
    assert parse_date("5 Şubat 2025") == "2025-02-05"
    assert parse_date("31.02.2025") is None       # olmayan tarih


def _good(**over):
    data = {"seller_vkn": make_vkn(random.Random(3)), "invoice_no": "ABC2025000000001",
            "invoice_date": "2025-03-12", "total": 120.0, "subtotal": 100.0, "vat_amount": 20.0, "vat_rate": 20}
    data.update(over)
    return data


def test_validate_clean_invoice_has_no_issues():
    assert validate(_good(), today=date(2025, 6, 1)) == []


def test_validate_total_mismatch_and_review():
    conf = {"total": 0.9, "subtotal": 0.9, "vat_amount": 0.9}
    issues = validate(_good(total=130.0), today=date(2025, 6, 1))
    assert any(i["code"] == "totals_mismatch" for i in issues)
    assert decide_review(issues, conf)


def test_validate_missing_required_and_future_date():
    issues = validate(_good(invoice_no=None, invoice_date="2030-01-01"), today=date(2025, 6, 1))
    codes = {i["code"] for i in issues}
    assert {"missing_field", "date_future"} <= codes


def test_validate_unusual_vat_rate_is_warning():
    issues = validate(_good(vat_rate=7, vat_amount=7.0, total=107.0), today=date(2025, 6, 1))
    assert any(i["code"] == "vat_rate_unusual" and i["severity"] == "warning" for i in issues)


def test_effective_confidence_recovers_after_fix():
    base = {"total": 0.9, "subtotal": 0.9, "vat_amount": 0.9}
    bad = validate(_good(total=130.0), today=date(2025, 6, 1))
    low = effective_confidence(base, bad)
    assert low["subtotal"] < 0.7 and low["total"] < 0.7
    assert base["subtotal"] == 0.9                      # depolanan değer değişmez
    good = validate(_good(), today=date(2025, 6, 1))
    assert effective_confidence(base, good) == base
