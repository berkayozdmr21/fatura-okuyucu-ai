"""Sentetik fatura/fiş üretici (PDF ve UBL-TR XML) + referans (ground truth) verisi.

Üretilen tüm VKN'ler gerçek firmalara ait DEĞİLDİR; sağlama algoritmasını geçecek şekilde rastgele üretilir.
Bu veri yalnızca test ve doğruluk ölçümü içindir. Gerçek dünya doğruluğu için gerçek (anonimleştirilmiş)
belgelerle ölçüm yapılmalıdır.
"""
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from fpdf import FPDF

_FONT_CANDIDATES = [
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]

COMPANY_PARTS = ["Anadolu", "Marmara", "Ege", "Karadeniz", "Yıldız", "Güneş", "Ay", "Çınar", "Ülker", "Şahin",
                 "Özkan", "Demir", "Kaya", "Işık", "Gökçe", "Bora", "Atlas", "Tuna"]
COMPANY_FIELDS = ["Gıda", "Tekstil", "İnşaat", "Bilişim", "Otomotiv", "Mobilya", "Lojistik", "Enerji", "Ticaret", "Kimya"]
SUFFIXES = ["A.Ş.", "Ltd. Şti.", "San. ve Tic. A.Ş.", "Tic. Ltd. Şti."]
MONTHS_TR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
VAT_RATES = [1, 10, 20, 20, 20, 8, 18]


def make_vkn(rng: random.Random) -> str:
    digits = [rng.randint(1, 9)] + [rng.randint(0, 9) for _ in range(8)]
    total = 0
    for i in range(9):
        tmp = (digits[i] + (9 - i)) % 10
        v = (tmp * (2 ** (9 - i))) % 9
        if tmp != 0 and v == 0:
            v = 9
        total += v
    digits.append((10 - total % 10) % 10)
    return "".join(map(str, digits))


def company(rng: random.Random) -> str:
    return f"{rng.choice(COMPANY_PARTS)} {rng.choice(COMPANY_FIELDS)} {rng.choice(SUFFIXES)}"


def fmt_amount(value: float, style: str) -> str:
    s = f"{value:,.2f}"                       # 1,234.56
    tr = s.replace(",", "X").replace(".", ",").replace("X", ".")   # 1.234,56
    return {"tl": f"{tr} TL", "sym": f"₺{tr}", "plain": tr}[style]


def fmt_date(d: date, style: str) -> str:
    if style == "dot":
        return d.strftime("%d.%m.%Y")
    if style == "slash":
        return d.strftime("%d/%m/%Y")
    return f"{d.day} {MONTHS_TR[d.month - 1]} {d.year}"


@dataclass
class Case:
    name: str
    content: bytes
    mime: str
    truth: Dict[str, object]
    kind: str                      # clean | bad_vkn | bad_total
    template: str


def _find_font() -> Optional[str]:
    for p in _FONT_CANDIDATES:
        if Path(p).is_file():
            return p
    return None


def _pdf(lines: List[str]) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    font = _find_font()
    if font:
        pdf.add_font("Body", "", font)
        pdf.set_font("Body", size=11)
    else:  # Türkçe karakter desteği yok; yine de çalışsın
        pdf.set_font("Helvetica", size=11)
        lines = [ln.encode("latin-1", "replace").decode("latin-1") for ln in lines]
    for ln in lines:
        pdf.cell(0, 7, ln, new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


def _ubl(truth: Dict[str, object]) -> bytes:
    t = truth
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
 xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
 xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
 <cbc:ID>{t['invoice_no']}</cbc:ID>
 <cbc:IssueDate>{t['invoice_date']}</cbc:IssueDate>
 <cbc:DocumentCurrencyCode>{t['currency']}</cbc:DocumentCurrencyCode>
 <cac:AccountingSupplierParty><cac:Party>
  <cac:PartyIdentification><cbc:ID schemeID="VKN">{t['seller_vkn']}</cbc:ID></cac:PartyIdentification>
  <cac:PartyName><cbc:Name>{t['seller_name']}</cbc:Name></cac:PartyName>
 </cac:Party></cac:AccountingSupplierParty>
 <cac:AccountingCustomerParty><cac:Party>
  <cac:PartyIdentification><cbc:ID schemeID="VKN">{t['buyer_vkn']}</cbc:ID></cac:PartyIdentification>
  <cac:PartyName><cbc:Name>{t['buyer_name']}</cbc:Name></cac:PartyName>
 </cac:Party></cac:AccountingCustomerParty>
 <cac:TaxTotal><cbc:TaxAmount currencyID="TRY">{t['vat_amount']:.2f}</cbc:TaxAmount>
  <cac:TaxSubtotal><cbc:TaxableAmount currencyID="TRY">{t['subtotal']:.2f}</cbc:TaxableAmount>
   <cbc:TaxAmount currencyID="TRY">{t['vat_amount']:.2f}</cbc:TaxAmount><cbc:Percent>{t['vat_rate']}</cbc:Percent>
   <cac:TaxCategory><cac:TaxScheme><cbc:TaxTypeCode>0015</cbc:TaxTypeCode></cac:TaxScheme></cac:TaxCategory>
  </cac:TaxSubtotal></cac:TaxTotal>
 <cac:LegalMonetaryTotal><cbc:TaxExclusiveAmount currencyID="TRY">{t['subtotal']:.2f}</cbc:TaxExclusiveAmount>
  <cbc:PayableAmount currencyID="TRY">{t['total']:.2f}</cbc:PayableAmount></cac:LegalMonetaryTotal>
</Invoice>""".encode("utf-8")


def _truth(rng: random.Random, i: int) -> Dict[str, object]:
    rate = rng.choice(VAT_RATES)
    subtotal = round(rng.uniform(50, 85000), 2)
    vat = round(subtotal * rate / 100, 2)
    d = date(2025, 1, 1) + timedelta(days=rng.randint(0, 600))
    prefix = "".join(rng.choice("ABCDEFGHJKLMNPRSTUVYZ") for _ in range(3))
    return {
        "seller_name": company(rng),
        "seller_vkn": make_vkn(rng),
        "buyer_name": company(rng),
        "buyer_vkn": make_vkn(rng),
        "invoice_no": f"{prefix}{d.year}{rng.randint(1, 999999999):09d}",
        "invoice_date": d.isoformat(),
        "currency": "TRY",
        "subtotal": subtotal,
        "vat_rate": rate,
        "vat_amount": vat,
        "total": round(subtotal + vat, 2),
    }


def _render(rng: random.Random, truth: Dict[str, object], template: str, shown: Dict[str, object]):
    """shown: belgede görünen değerler (hatalı vakalarda truth'tan farklı olabilir)."""
    a = rng.choice(["tl", "sym", "plain"])
    ds = rng.choice(["dot", "slash", "text"])
    d = date.fromisoformat(truth["invoice_date"])  # type: ignore[arg-type]
    amt = lambda v: fmt_amount(float(v), a)  # noqa: E731
    rate = truth["vat_rate"]

    if template == "A":   # etiket: değer aynı satırda, e-Arşiv tarzı
        lines = [
            str(truth["seller_name"]), "e-Arşiv Fatura", f"VKN: {shown['seller_vkn']}",
            f"Fatura No: {truth['invoice_no']}", f"Fatura Tarihi: {fmt_date(d, ds)}", "",
            "SAYIN", str(truth["buyer_name"]), f"VKN: {truth['buyer_vkn']}", "",
            f"Mal Hizmet Toplam Tutarı: {amt(truth['subtotal'])}",
            f"Hesaplanan KDV(%{rate}): {amt(truth['vat_amount'])}",
            f"Vergiler Dahil Toplam Tutar: {amt(shown['total'])}",
        ]
    elif template == "B":  # etiket ve değer ayrı satırlarda
        lines = [
            "SATICI", str(truth["seller_name"]), "Vergi Kimlik No", str(shown["seller_vkn"]),
            "Fatura Numarası", str(truth["invoice_no"]), "Düzenleme Tarihi", fmt_date(d, ds), "",
            "ALICI", str(truth["buyer_name"]), "Vergi Kimlik No", str(truth["buyer_vkn"]), "",
            "KDV Hariç Toplam", amt(truth["subtotal"]),
            f"Toplam KDV (%{rate})", amt(truth["vat_amount"]),
            "Ödenecek Tutar", amt(shown["total"]),
        ]
    else:                  # C: market/perakende fişi
        lines = [
            str(truth["seller_name"]), f"V.K.N. {shown['seller_vkn']}", f"FİŞ NO: {truth['invoice_no']}",
            f"TARİH: {fmt_date(d, 'dot')}", "",
            f"KDV %{rate}  {amt(truth['vat_amount'])}",
            f"TOPKDV  {amt(truth['vat_amount'])}", f"TOPLAM  {amt(shown['total'])}",
        ]
    return _pdf(lines)


def generate(n: int = 60, seed: int = 7, bad_ratio: float = 0.2) -> List[Case]:
    rng = random.Random(seed)
    cases: List[Case] = []
    for i in range(n):
        truth = _truth(rng, i)
        template = ["A", "B", "C", "X"][i % 4]
        kind = "clean"
        shown = dict(truth)
        roll = rng.random()
        if roll < bad_ratio / 2:
            kind = "bad_vkn"
            vkn = str(truth["seller_vkn"])
            wrong = str((int(vkn[-1]) + rng.randint(1, 9)) % 10)
            shown["seller_vkn"] = vkn[:-1] + wrong
        elif roll < bad_ratio:
            kind = "bad_total"
            shown["total"] = round(float(truth["total"]) + rng.choice([10.0, 25.5, 100.0]), 2)

        if template == "X":
            truth_x = dict(truth)
            content = _ubl({**truth_x, **{k: shown[k] for k in ("seller_vkn", "total")}})
            mime, name = "application/xml", f"case_{i:03d}.xml"
        else:
            if template == "C":
                truth = {**truth, "buyer_name": None, "buyer_vkn": None}
            content = _render(rng, truth, template, shown)
            mime, name = "application/pdf", f"case_{i:03d}.pdf"
        cases.append(Case(name, content, mime, truth, kind, template))
    return cases
