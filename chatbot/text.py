"""Türkçe metin normalizasyonu ve basit kök bulma."""
import re
import unicodedata
from typing import List, Set

_TR_MAP = str.maketrans({"ı": "i", "İ": "i", "I": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
                         "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"})

STOPWORDS: Set[str] = {
    "bir", "bu", "su", "o", "ve", "ile", "icin", "ben", "benim", "bana", "beni", "var", "yok", "mi", "mu",
    "da", "de", "ki", "ama", "veya", "gibi", "kadar", "daha", "cok", "en", "ne", "nasil", "nerede", "nereden",
    "nereye", "nerde", "neden", "niye", "hangi", "istiyorum", "istedim", "lazim", "gerek", "olur", "olarak",
    "yapmak", "yapabilir", "miyim", "misin", "musun", "bulabilirim", "gorebilirim", "bulamiyorum", "goremiyorum",
    "sey", "seyi", "acaba", "lutfen", "bunu", "sunu", "onu", "nedir", "midir", "olan", "ise", "oldu", "olmuyor",
    "alirim", "alabilirim", "yaparim", "yapilir", "edilir", "eder", "yapmaliyim", "yapmam", "yapabilirim",
    "ediyor", "diyor", "gelmiyor", "cikiyor", "yapiyor",
}


def fold(text: str) -> str:
    text = text.translate(_TR_MAP).lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def stem(token: str) -> str:
    """Kaba kök: Türkçe ekleri atmak yerine ilk 5 harfi kullanır ('yükleyemiyorum' -> 'yukle')."""
    return token if len(token) <= 5 else token[:5]


def tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", fold(text))


def stems(text: str, drop_stopwords: bool = True) -> List[str]:
    out = []
    for t in tokens(text):
        if drop_stopwords and t in STOPWORDS:
            continue
        if len(t) < 2 and not t.isdigit():
            continue
        out.append(stem(t))
    return out
