"""UBL-TR (e-Fatura / e-Arşiv) XML okuyucu. Yapısal olduğu için güven skoru yüksektir."""
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Tuple

from .parsing import only_digits
from .schema import empty_data


def _text(node: Optional[ET.Element]) -> Optional[str]:
    return node.text.strip() if node is not None and node.text and node.text.strip() else None


def _num(node: Optional[ET.Element]) -> Optional[float]:
    t = _text(node)
    try:
        return round(float(t), 2) if t is not None else None
    except ValueError:
        return None


def _party(root: ET.Element, container: str) -> Tuple[Optional[str], Optional[str]]:
    """(unvan, vergi no) döner. container: AccountingSupplierParty | AccountingCustomerParty"""
    node = root.find(f".//{{*}}{container}/{{*}}Party")
    if node is None:
        return None, None
    name = _text(node.find("./{*}PartyName/{*}Name"))
    if not name:  # Gerçek kişi ise ad soyad Person altında olur
        person = node.find("./{*}Person")
        if person is not None:
            first, family = _text(person.find("{*}FirstName")), _text(person.find("{*}FamilyName"))
            name = " ".join(p for p in (first, family) if p) or None
    tax_id = None
    for ident in node.findall("./{*}PartyIdentification/{*}ID"):
        scheme = (ident.get("schemeID") or "").upper()
        if scheme in ("VKN", "TCKN") and _text(ident):
            tax_id = only_digits(_text(ident))
            break
    return name, tax_id


def parse_ubl(xml_bytes: bytes) -> Tuple[Dict[str, object], Dict[str, float]]:
    # Güvenlik: UBL-TR faturalarında DOCTYPE/ENTITY bulunmaz. Varlık genişletme saldırılarını
    # (billion laughs) önlemek için bunları içeren dosyaları baştan reddediyoruz.
    upper = xml_bytes.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ValueError("DOCTYPE/ENTITY içeren XML kabul edilmez")
    root = ET.fromstring(xml_bytes)
    if not root.tag.endswith("Invoice"):
        raise ValueError("UBL Invoice kök elemanı bulunamadı")

    data = empty_data()
    data["invoice_no"] = _text(root.find("{*}ID"))
    data["invoice_date"] = _text(root.find("{*}IssueDate"))
    data["currency"] = _text(root.find("{*}DocumentCurrencyCode")) or "TRY"
    data["seller_name"], data["seller_vkn"] = _party(root, "AccountingSupplierParty")
    data["buyer_name"], data["buyer_vkn"] = _party(root, "AccountingCustomerParty")

    monetary = root.find("{*}LegalMonetaryTotal")
    if monetary is not None:
        data["subtotal"] = _num(monetary.find("{*}TaxExclusiveAmount"))
        data["total"] = _num(monetary.find("{*}PayableAmount")) or _num(monetary.find("{*}TaxInclusiveAmount"))

    tax_total = root.find("{*}TaxTotal")
    if tax_total is not None:
        data["vat_amount"] = _num(tax_total.find("{*}TaxAmount"))
        rates = {
            _num(sub.find("{*}Percent"))
            for sub in tax_total.findall("{*}TaxSubtotal")
            if sub.find("{*}TaxCategory/{*}TaxScheme/{*}TaxTypeCode") is None
            or _text(sub.find("{*}TaxCategory/{*}TaxScheme/{*}TaxTypeCode")) == "0015"  # 0015 = KDV
        }
        rates.discard(None)
        if len(rates) == 1:
            data["vat_rate"] = rates.pop()
            if data["vat_rate"] is not None and float(data["vat_rate"]).is_integer():
                data["vat_rate"] = int(data["vat_rate"])

    confidence = {k: 0.99 for k, v in data.items() if v is not None}
    return data, confidence
