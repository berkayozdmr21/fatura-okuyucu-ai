"""Türkçe sayı, tarih ve metin normalizasyonu."""
import re
import unicodedata
from datetime import date
from typing import Optional

_TR_MONTHS = {
    "ocak": 1, "subat": 2, "mart": 3, "nisan": 4, "mayis": 5, "haziran": 6,
    "temmuz": 7, "agustos": 8, "eylul": 9, "ekim": 10, "kasim": 11, "aralik": 12,
}

_TR_MAP = str.maketrans({"ı": "i", "İ": "i", "I": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
                         "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"})


def fold(text: str) -> str:
    """Büyük/küçük harf ve Türkçe karakter farkını yok sayan karşılaştırma biçimi."""
    text = text.translate(_TR_MAP).lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


_AMOUNT_RE = re.compile(r"-?\d[\d.,\s]*\d|\d")


def parse_amount(raw: str) -> Optional[float]:
    """'1.234,56 TL', '₺1,234.56', '1234.5' gibi metinleri sayıya çevirir."""
    if raw is None:
        return None
    m = _AMOUNT_RE.search(raw.replace(" ", " "))
    if not m:
        return None
    s = m.group(0).replace(" ", "")
    has_dot, has_comma = "." in s, "," in s
    if has_dot and has_comma:
        # Son görülen ayraç ondalık ayraçtır
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif has_comma:
        head, _, tail = s.rpartition(",")
        # Türkçe'de virgül ondalık ayraçtır (12,5 / 1234,56). Birden çok virgül binlik ayracıdır.
        if s.count(",") > 1:
            s = s.replace(",", "")
        else:
            s = head + "." + tail
    elif has_dot:
        head, _, tail = s.rpartition(".")
        if s.count(".") > 1 or len(tail) == 3:
            # 1.234 veya 1.234.567 -> binlik ayracı (Türkçe)
            s = s.replace(".", "")
    try:
        return round(float(s), 2)
    except ValueError:
        return None


_DATE_NUM = re.compile(r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})")
_DATE_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_DATE_TXT = re.compile(r"(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(\d{4})")


def parse_date(raw: str) -> Optional[str]:
    """Çeşitli tarih biçimlerini ISO (YYYY-MM-DD) metnine çevirir; geçersizse None."""
    if not raw:
        return None
    candidates = []
    m = _DATE_ISO.search(raw)
    if m:
        candidates.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
    m = _DATE_NUM.search(raw)
    if m:
        candidates.append((int(m.group(3)), int(m.group(2)), int(m.group(1))))
    m = _DATE_TXT.search(raw)
    if m and fold(m.group(2)) in _TR_MONTHS:
        candidates.append((int(m.group(3)), _TR_MONTHS[fold(m.group(2))], int(m.group(1))))
    for y, mo, d in candidates:
        try:
            return date(y, mo, d).isoformat()
        except ValueError:
            continue
    return None


def only_digits(raw: str) -> str:
    return re.sub(r"\D", "", raw or "")
