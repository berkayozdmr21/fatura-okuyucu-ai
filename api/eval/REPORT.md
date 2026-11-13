# Doğruluk raporu (sentetik veri)

> Bu sonuçlar **sentetik** faturalarla ölçüldü (`eval/generate.py`). Şablonlar çözümleyiciyi yazarken bilinen biçimlerdir; gerçek dünya doğruluğu bunun altında olacaktır. Gerçek, anonimleştirilmiş belgelerle ayrıca ölçülmelidir.

- Belge sayısı: **400** (seed=11), toplam süre: 0.90 sn (2.2 ms/belge)
- Çıkarıcılar: {'pdf_text': 300, 'ubl_xml': 100}

## Alan bazında doğruluk (hatasız belgelerde)

| Alan | Doğru / Toplam | Doğruluk |
|---|---|---|
| `seller_name` | 318 / 318 | %100.0 |
| `seller_vkn` | 318 / 318 | %100.0 |
| `buyer_name` | 318 / 318 | %100.0 |
| `buyer_vkn` | 318 / 318 | %100.0 |
| `invoice_no` | 318 / 318 | %100.0 |
| `invoice_date` | 318 / 318 | %100.0 |
| `currency` | 318 / 318 | %100.0 |
| `subtotal` | 318 / 318 | %100.0 |
| `vat_rate` | 318 / 318 | %100.0 |
| `vat_amount` | 318 / 318 | %100.0 |
| `total` | 318 / 318 | %100.0 |

## Şablon bazında tam doğru belge oranı

| Şablon | Tam doğru | Oran |
|---|---|---|
| A: etiket:değer aynı satır (e-Arşiv) | 83 / 83 | %100.0 |
| B: etiket ve değer ayrı satır | 80 / 80 | %100.0 |
| C: perakende fişi | 83 / 83 | %100.0 |
| X: UBL-TR XML | 72 / 72 | %100.0 |

## Hata yakalama (doğrulama kuralları)

- Bilinçli bozulmuş belgeler (yanlış VKN veya toplam): **82 / 82** incelemeye işaretlendi (%100.0)
- Temiz belgelerde gereksiz inceleme (yanlış alarm): **0 / 318** (%0.0)

## OCR hattı (PDF -> görüntü -> yerel OCR)

> Temiz render edilmiş görüntüler; gerçek telefon fotoğraflarında (eğiklik, gölge, buruşuk fiş) sonuç düşer.

- Belge: **79**, tüm alanları doğru: **53** (%67.1)
- İncelemeye işaretlenen: **26**
- **Sessiz hata** (yanlış okundu ama işaretlenmedi): **0**
