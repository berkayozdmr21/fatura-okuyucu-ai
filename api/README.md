# api

FastAPI arka uç: kimlik doğrulama, belge yükleme, fatura çıkarımı, doğrulama, inceleme/onay ve Excel/CSV dışa aktarım.

## Çalıştırma

```bash
cd api
python -m venv .venv && .venv\Scripts\activate      # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env                           # JWT_SECRET'i değiştir!
uvicorn app.main:app --reload --port 8000
```

Etkileşimli belge: http://localhost:8000/docs

İsteğe bağlı yerel OCR (fotoğraf ve taranmış PDF için): `pip install rapidocr-onnxruntime`

## Testler ve ölçüm

```bash
python -m pytest -q                                   # 124 test
python -m eval.run_eval --n 400 --seed 11 --ocr       # eval/REPORT.md üretir
```

## Çıkarım hattı

```
dosya ─┬─ .xml  ──► UBL-TR okuyucu ───────────────┐
       ├─ .pdf  ──► metin katmanı ► kural çözümleyici ─┤
       │            (metin yoksa: sayfa ► OCR) ──────┼─► doğrulama ─► needs_review?
       └─ .png/.jpg/.webp ► OCR ► kural çözümleyici ─┘
                                                         (isteğe bağlı, EXTRACTION_MODE=hybrid)
                                                         belirsizse Claude ile ikinci okuma
```

**Doğrulama kuralları:** VKN (10 hane) ve TCKN (11 hane) sağlama toplamı, matrah + KDV = toplam, matrah × oran = KDV,
alışılmadık KDV oranı, tarih makullüğü, zorunlu alanlar, aynı satıcı+fatura no tekrarı.

**Güven yaklaşımı:** Depolanan güven skoru çıkarıcının ham skorudur. Sorunların yarattığı şüphe anlık hesaplanır
(`effective_confidence`); bir alan düzeltilince sorun kalkar ve diğer alanların güveni kendiliğinden toparlanır.

## Gizlilik ve güvenlik

- **Varsayılan `EXTRACTION_MODE=local`:** hiçbir belge dışarı gönderilmez. `hybrid` modda yalnızca yerel okuma yetersizse
  belge Anthropic API'sine gönderilir; bunu müşterine açıkça söylemelisin (KVKK).
- Dosyalar `STORAGE_DIR` altında içerik özetiyle adlandırılır (yol manipülasyonu mümkün değil), `RETENTION_DAYS` sonra silinir:
  `python -m app.cli purge` (zamanlanmış görev olarak çalıştır).
- Şifreler PBKDF2-SHA256 (260k iterasyon) ile özetlenir; JWT ile oturum; başarısız girişler sınırlanır.
- Yükleme: uzantı beyaz listesi + dosya içeriği (magic bytes) kontrolü + boyut sınırı. XML'de DOCTYPE/ENTITY reddedilir.
- Dışa aktarımda formül enjeksiyonuna karşı (`=`, `+`, `-`, `@`) hücreler tırnakla korunur.
- Veri izolasyonu: her sorgu `org_id` ile sınırlıdır; müşteri yalnızca kendi belgelerini görür (testlerle doğrulanır).

## Uç noktalar

| Yöntem | Yol | Yetki |
|---|---|---|
| POST | `/auth/register`, `/auth/login` | herkes |
| GET | `/auth/me`, `/auth/org` | giriş yapmış |
| POST | `/documents` (multipart `file`) | giriş yapmış |
| GET | `/documents`, `/documents/{id}`, `/documents/{id}/file` | giriş yapmış (kapsam: müşteri=kendi, muhasebeci=büro) |
| PATCH | `/documents/{id}` (alan düzeltme, onay/red) | muhasebeci |
| DELETE | `/documents/{id}` | muhasebeci / müşteri (onaylanmamışsa) |
| GET | `/exports/documents.xlsx`, `/exports/documents.csv` | muhasebeci |
| POST | `/chat` | giriş yapmış (`chatbot` modülü varsa) |

## Bilinen sınırlar

- Çıkarım kuralları sentetik şablonlarla geliştirildi; gerçek faturalarda doğruluk daha düşük olacaktır (bkz. `eval/REPORT.md`).
- Kalem (satır) bazlı çıkarım yok, yalnızca başlık ve toplam alanları okunur.
- Dışa aktarım genel bir tablo biçimindedir; Logo/Mikro/Luca'ya özel içe aktarma şablonları yapılmadı.
- Bellek içi giriş sınırlayıcı tek sunucuda çalışır; çok sunuculu kurulumda Redis gibi ortak bir depo gerekir.
- LLM (`hybrid`) yolu canlı API anahtarıyla test edilmedi; yalnızca yanıt ayrıştırma birim mantığı ve devre dışı davranışı doğrulandı.
- Claude yanıtı `refusal` ile biterse yerel sonuca düşülür; sunucu taraflı yedek model (`fallbacks`) etkinleştirilmedi.
