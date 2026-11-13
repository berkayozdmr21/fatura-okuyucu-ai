"""Çıkarılan fatura verisinin şeması ve sonuç tipi."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Veri alanları (hepsi isteğe bağlıdır; eksik alan None kalır)
FIELDS = [
    "seller_name",
    "seller_vkn",
    "buyer_name",
    "buyer_vkn",
    "invoice_no",
    "invoice_date",
    "currency",
    "subtotal",     # matrah (KDV hariç)
    "vat_rate",     # KDV oranı (%)
    "vat_amount",
    "total",
]

# Bunlar olmadan kayıt muhasebeleştirilemez
REQUIRED = ["seller_vkn", "invoice_no", "invoice_date", "total"]


def empty_data() -> Dict[str, Optional[object]]:
    return {f: None for f in FIELDS}


@dataclass
class ExtractionResult:
    data: Dict[str, Optional[object]] = field(default_factory=empty_data)
    confidence: Dict[str, float] = field(default_factory=dict)
    issues: List[dict] = field(default_factory=list)
    needs_review: bool = False
    extractor: str = "none"
    raw_text: str = ""
    failed: bool = False
