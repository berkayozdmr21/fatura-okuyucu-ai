"""Doğrulama kuralları: VKN/TCKN sağlama toplamı, KDV ve toplam tutarlılığı, tarih makullüğü.

Doğrulayıcılar güven skorlarını DEĞİŞTİRMEZ. Her sorun hangi alanları ne kadar şüpheli yaptığını
(`affects`, `cap`) kendi içinde taşır; `effective_confidence` bunu anlık hesaplar. Böylece bir alan
düzeltilip sorun ortadan kalktığında diğer alanların güveni de kendiliğinden toparlanır.
"""
from datetime import date, timedelta
from typing import Dict, List, Optional

from .schema import REQUIRED

VALID_VAT_RATES = {0, 1, 8, 10, 18, 20}
AMOUNT_TOLERANCE = 0.02   # kuruş yuvarlama toleransı (matrah + KDV = toplam)
VAT_TOLERANCE = 0.10      # matrah x oran = KDV kontrolü için tolerans (satır bazlı yuvarlama)
LOW_CONFIDENCE = 0.7


def is_valid_vkn(vkn: str) -> bool:
    """10 haneli Vergi Kimlik Numarası sağlama algoritması."""
    if not vkn or len(vkn) != 10 or not vkn.isdigit():
        return False
    digits = [int(c) for c in vkn]
    total = 0
    for i in range(9):
        tmp = (digits[i] + (9 - i)) % 10
        v = (tmp * (2 ** (9 - i))) % 9
        if tmp != 0 and v == 0:
            v = 9
        total += v
    return (10 - total % 10) % 10 == digits[9]


def is_valid_tckn(tckn: str) -> bool:
    """11 haneli T.C. Kimlik Numarası algoritması."""
    if not tckn or len(tckn) != 11 or not tckn.isdigit() or tckn[0] == "0":
        return False
    d = [int(c) for c in tckn]
    odd = d[0] + d[2] + d[4] + d[6] + d[8]
    even = d[1] + d[3] + d[5] + d[7]
    if (odd * 7 - even) % 10 != d[9]:
        return False
    return sum(d[:10]) % 10 == d[10]


def check_tax_id(value: Optional[str]) -> Optional[str]:
    """Geçerliyse None, değilse sorun kodu döner."""
    if not value:
        return None
    if len(value) == 10:
        return None if is_valid_vkn(value) else "vkn_invalid"
    if len(value) == 11:
        return None if is_valid_tckn(value) else "tckn_invalid"
    return "tax_id_length"


def _issue(code: str, field: str, severity: str, message: str, cap: float = 0.4,
           affects: Optional[List[str]] = None) -> dict:
    return {"code": code, "field": field, "severity": severity, "message": message,
            "cap": cap, "affects": affects or [field]}


def validate(data: Dict[str, object], today: Optional[date] = None) -> List[dict]:
    """Verideki tutarsızlıkları döner."""
    today = today or date.today()
    issues: List[dict] = []

    for f in REQUIRED:
        if data.get(f) in (None, ""):
            issues.append(_issue("missing_field", f, "error", f"Zorunlu alan okunamadı: {f}", cap=0.0))

    for f, label in (("seller_vkn", "Satıcı"), ("buyer_vkn", "Alıcı")):
        problem = check_tax_id(data.get(f))
        if problem:
            messages = {
                "vkn_invalid": f"{label} VKN sağlama toplamı hatalı (yanlış okunmuş olabilir).",
                "tckn_invalid": f"{label} TCKN geçersiz.",
                "tax_id_length": f"{label} vergi numarası 10 veya 11 haneli olmalı.",
            }
            issues.append(_issue(problem, f, "error", messages[problem], cap=0.3))

    subtotal, vat, total = data.get("subtotal"), data.get("vat_amount"), data.get("total")
    rate = data.get("vat_rate")

    if rate is not None and rate not in VALID_VAT_RATES:
        issues.append(_issue("vat_rate_unusual", "vat_rate", "warning", f"Alışılmadık KDV oranı: %{rate}"))

    if subtotal is not None and vat is not None and total is not None:
        if abs(subtotal + vat - total) > AMOUNT_TOLERANCE:
            issues.append(_issue(
                "totals_mismatch", "total", "error",
                f"Matrah + KDV = {round(subtotal + vat, 2)} ama toplam {total}.",
                affects=["subtotal", "vat_amount", "total"]))

    if subtotal is not None and vat is not None and rate is not None:
        expected = round(subtotal * rate / 100, 2)
        # Satır bazlı yuvarlama birkaç kuruş fark yaratabilir; daha büyük fark inceleme gerektirir
        if abs(expected - vat) > VAT_TOLERANCE:
            issues.append(_issue(
                "vat_mismatch", "vat_amount", "warning",
                f"%{rate} KDV beklenen {expected}, okunan {vat}.", cap=0.5))

    d = data.get("invoice_date")
    if d:
        try:
            parsed = date.fromisoformat(str(d))
            if parsed > today + timedelta(days=1):
                issues.append(_issue("date_future", "invoice_date", "error", "Fatura tarihi gelecekte.", cap=0.3))
            elif parsed < today - timedelta(days=365 * 10):
                issues.append(_issue("date_old", "invoice_date", "warning", "Fatura tarihi 10 yıldan eski."))
        except ValueError:
            issues.append(_issue("date_invalid", "invoice_date", "error", "Tarih geçersiz.", cap=0.3))

    return issues


def effective_confidence(base: Dict[str, float], issues: List[dict]) -> Dict[str, float]:
    """Çıkarıcının ham güveni + sorunların yarattığı şüphe. Depolanan değerleri değiştirmez."""
    out = dict(base or {})
    for issue in issues or []:
        if issue.get("code") == "missing_field":
            continue
        for f in issue.get("affects") or ([issue["field"]] if issue.get("field") else []):
            if f in out:
                out[f] = min(out[f], issue.get("cap", 0.5))
    return out


def decide_review(issues: List[dict], base_confidence: Dict[str, float]) -> bool:
    if any(i["severity"] == "error" for i in issues):
        return True
    return any(c < LOW_CONFIDENCE for c in effective_confidence(base_confidence, issues).values())
