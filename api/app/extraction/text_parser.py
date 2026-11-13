"""Düz metinden (PDF metin katmanı veya OCR çıktısı) fatura alanlarını çıkaran kural tabanlı çözümleyici."""
import re
from typing import Dict, List, Optional, Tuple

from .parsing import fold, only_digits, parse_amount, parse_date
from .schema import empty_data

_AMOUNT_TOKEN = re.compile(r"\d[\d.,]*\d|\d")
_COMPANY_SUFFIX = re.compile(
    r"\b(a\.?\s?s\.?|ltd\.?|sti\.?|anonim|limited|san\.?|tic\.?|koll\.?|şirketi|sirketi)\b|\b(a\.?s|a\.?ş)\b"
)
_SELLER_MARK = re.compile(r"^\s*(satici|duzenleyen|gonderen|firma)\b")
_BUYER_MARK = re.compile(r"(^\s*(alici|sayin|musteri|teslim edilen)\b)|\balici\b")

_SUBTOTAL = re.compile(
    r"(mal\s*hizmet\s*toplam|kdv\s*haric|vergi\s*haric|matrah|ara\s*toplam|kdv\s*siz)"
)
_TOTAL = re.compile(
    r"(genel\s*toplam|odenecek\s*tutar|vergiler\s*dahil|kdv\s*dahil|toplam\s*tutar|tahsil\s*edilen)"
)
_VAT_TOTAL = re.compile(r"(hesaplanan\s*kdv|toplam\s*kdv|kdv\s*toplam|kdv\s*tutari|topkdv|top\.?\s*kdv)")
_VAT_RATE_LINE = re.compile(r"\bkdv\b.{0,12}%\s*\d|\bkdv\s*\(?\s*\d{1,2}\s*\)?\s*[:\s]")
# OCR boşlukları yutabilir ("TOPLAM45.022,45"), bu yüzden \b yerine "harf devam etmiyor" koşulu
_TOTAL_FALLBACK = re.compile(r"^\W*toplam(?![a-z])")

_INVOICE_NO_LABEL = re.compile(
    r"(fatura\s*(no|numarasi|numara|sira\s*no)|belge\s*(no|numarasi)|fis\s*(no|numarasi)|seri\s*sira)\b"
)
_INVOICE_NO_VALUE = re.compile(r"[a-z0-9][a-z0-9\-/_.]{2,24}")
_DATE_LABEL = re.compile(r"(fatura\s*tarihi|duzenleme\s*tarihi|belge\s*tarihi|fis\s*tarihi|\btarih\b)")
_TAXID_LABEL = re.compile(r"(\bvkn\b|v\.?\s?k\.?\s?n\.?|vergi\s*(kimlik\s*)?(no|numarasi)|\btckn\b|t\.?c\.?\s*kimlik)")
_TAXID_VALUE = re.compile(r"(?<!\d)(\d{10,11})(?!\d)")
# Doğrudan okunamayıp diğer alanlardan hesaplanan veya varsayılan değerlerin güveni (inceleme eşiğinin üstünde)
DERIVED_CONF = 0.75
# Oran: %20, (20) veya "kdv 20". Tutarın ("kdv 2.704,90") oran sanılmaması için sayının ardında ayraç olmamalı.
_RATE = re.compile(r"%\s*(\d{1,2})|\(\s*(\d{1,2})\s*\)|kdv\s*(\d{1,2})(?![\d.,])")


def _last_amount(s: str) -> Optional[float]:
    tokens = _AMOUNT_TOKEN.findall(s)
    for tok in reversed(tokens):
        val = parse_amount(tok)
        if val is not None:
            return val
    return None


def _strip_label(line: str) -> str:
    """'Satıcı: ABC Ltd.' -> 'ABC Ltd.'"""
    if ":" in line:
        head, _, tail = line.partition(":")
        if len(head) <= 30 and tail.strip():
            return tail.strip()
    return line.strip()


def parse_text(text: str) -> Tuple[Dict[str, object], Dict[str, float]]:
    data = empty_data()
    conf: Dict[str, float] = {}

    lines: List[str] = [ln.strip() for ln in text.splitlines() if ln.strip()]
    folded = [fold(ln) for ln in lines]

    def nxt(i: int, k: int = 1) -> str:
        return folded[i + k] if i + k < len(folded) else ""

    def set_field(name: str, value, c: float) -> None:
        if value is not None and (name not in conf or c > conf[name]):
            data[name] = value
            conf[name] = c

    # ---- Taraflar (satıcı / alıcı), VKN ve unvanlar ----
    party = "seller"
    seller_name_pending = False
    buyer_name_pending = False
    for i, (orig, fl) in enumerate(zip(lines, folded)):
        if _SELLER_MARK.search(fl):
            party = "seller"
            seller_name_pending = True
        elif _BUYER_MARK.search(fl):
            party = "buyer"
            buyer_name_pending = True

        has_company = bool(_COMPANY_SUFFIX.search(fl))
        pending = seller_name_pending if party == "seller" else buyer_name_pending
        if (has_company or pending) and not _TAXID_LABEL.search(fl):
            name_key = "seller_name" if party == "seller" else "buyer_name"
            candidate = _strip_label(orig)
            label_only = fl.strip(" :") in ("satici", "alici", "sayin", "musteri", "duzenleyen")
            if candidate and not label_only and name_key not in conf and not re.fullmatch(r"[\d\W]+", candidate):
                set_field(name_key, candidate, 0.85 if has_company else 0.6)
                if party == "seller":
                    seller_name_pending = False
                else:
                    buyer_name_pending = False

        if _TAXID_LABEL.search(fl):
            m = _TAXID_VALUE.search(fl) or _TAXID_VALUE.search(nxt(i))
            if m:
                key = "seller_vkn" if party == "seller" else "buyer_vkn"
                if key not in conf:
                    set_field(key, only_digits(m.group(1)), 0.9)

    if "seller_name" not in conf and lines:
        set_field("seller_name", lines[0], 0.4)

    # ---- Fatura numarası ----
    for i, fl in enumerate(folded):
        m = _INVOICE_NO_LABEL.search(fl)
        if not m:
            continue
        rest = fl[m.end():]
        for chunk in (rest, nxt(i)):
            for cand in _INVOICE_NO_VALUE.findall(chunk):
                if any(ch.isdigit() for ch in cand) and not parse_date(cand):
                    set_field("invoice_no", cand.upper(), 0.9)
                    break
            if "invoice_no" in conf:
                break
        if "invoice_no" in conf:
            break

    # ---- Tarih ----
    for i, fl in enumerate(folded):
        m = _DATE_LABEL.search(fl)
        if m:
            d = parse_date(fl[m.end():]) or parse_date(nxt(i))
            if d:
                strong = "fatura" in m.group(0) or "duzenleme" in m.group(0)
                set_field("invoice_date", d, 0.9 if strong else 0.8)
                break
    if "invoice_date" not in conf:
        d = parse_date(" ".join(lines))
        if d:
            set_field("invoice_date", d, 0.5)

    # ---- Tutarlar ----
    vat_total_value: Optional[float] = None
    vat_total_rate: Optional[int] = None
    vat_rate_lines: List[Tuple[Optional[int], float]] = []
    bare_total: Optional[float] = None

    for i, fl in enumerate(folded):
        # "%20" gibi oranlar tutar sayılmasın
        stripped = re.sub(r"%\s*\d{1,3}(?:[.,]\d+)?", " ", fl)
        amount = _last_amount(stripped) if _AMOUNT_TOKEN.search(stripped) else None
        if _SUBTOTAL.search(fl):
            amt = amount if amount is not None else _last_amount(nxt(i))
            if amt is not None and "subtotal" not in conf:
                set_field("subtotal", amt, 0.9)
        elif _TOTAL.search(fl):
            amt = amount if amount is not None else _last_amount(nxt(i))
            if amt is not None and "total" not in conf:
                set_field("total", amt, 0.9)
        elif _VAT_TOTAL.search(fl):
            amt = amount if amount is not None else _last_amount(nxt(i))
            if amt is not None and vat_total_value is None:
                vat_total_value = amt
                rm = _RATE.search(fl)
                if rm:
                    vat_total_rate = int(next(g for g in rm.groups() if g))
        elif _VAT_RATE_LINE.search(fl):
            rm = _RATE.search(fl)
            rate = int(next(g for g in rm.groups() if g)) if rm else None
            if amount is not None:
                vat_rate_lines.append((rate, amount))
        elif _TOTAL_FALLBACK.search(fl) and bare_total is None and amount is not None:
            bare_total = amount

    if "total" not in conf and bare_total is not None:
        set_field("total", bare_total, 0.7)

    if vat_total_value is not None:
        set_field("vat_amount", vat_total_value, 0.9)
        rates = {r for r, _ in vat_rate_lines if r is not None}
        if vat_total_rate is not None:
            set_field("vat_rate", vat_total_rate, 0.85)
        elif len(rates) == 1:
            set_field("vat_rate", rates.pop(), 0.85)
    elif vat_rate_lines:
        set_field("vat_amount", round(sum(a for _, a in vat_rate_lines), 2), 0.8)
        rates = {r for r, _ in vat_rate_lines if r is not None}
        if len(rates) == 1:
            set_field("vat_rate", rates.pop(), 0.85)

    # Eksik olanı diğer ikisinden türet (daha düşük güvenle)
    total, sub, vat = data.get("total"), data.get("subtotal"), data.get("vat_amount")
    if sub is None and total is not None and vat is not None:
        set_field("subtotal", round(total - vat, 2), DERIVED_CONF)
    elif vat is None and total is not None and sub is not None:
        set_field("vat_amount", round(total - sub, 2), DERIVED_CONF)
    if data.get("vat_rate") is None and data.get("subtotal") and data.get("vat_amount") is not None:
        implied = round(100 * data["vat_amount"] / data["subtotal"])  # type: ignore[operator]
        if implied in (0, 1, 8, 10, 18, 20):
            set_field("vat_rate", implied, DERIVED_CONF)

    # ---- Para birimi ----
    joined = " ".join(lines)
    if re.search(r"\$|\busd\b", joined, re.I):
        set_field("currency", "USD", 0.8)
    elif re.search(r"€|\beur\b", joined, re.I):
        set_field("currency", "EUR", 0.8)
    elif re.search(r"₺|\btl\b|\btry\b", joined, re.I):
        set_field("currency", "TRY", 0.9)
    else:
        set_field("currency", "TRY", DERIVED_CONF)

    return data, conf

