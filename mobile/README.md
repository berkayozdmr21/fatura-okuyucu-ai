# mobile

Mobil uygulama (Expo / React Native, TypeScript). Telefonda fiş ve fatura fotoğrafı çekip doğrudan yüklemek,
belgeleri görmek ve yardım asistanına sormak için. Aynı hesapla web ve masaüstü uygulamasına da girilir; veriler ortaktır.

## Çalıştırma

```bash
cd mobile
npm install --legacy-peer-deps
# API adresini ver (gizli bilgi değildir):
#   Android emülatörü   -> http://10.0.2.2:8000
#   Gerçek telefon      -> http://<bilgisayarın yerel IP'si>:8000   (API'yi --host 0.0.0.0 ile başlat)
EXPO_PUBLIC_API_URL=http://10.0.2.2:8000 npx expo start      # Windows PowerShell: $env:EXPO_PUBLIC_API_URL="..."
npm test            # mantık birim testleri (vitest)
npm run typecheck   # TypeScript denetimi
```

Telefonda denemek için Expo Go uygulamasıyla QR kodu okut. Üretimde API adresi **HTTPS** olmalıdır.
Mağaza yayını için EAS Build gerekir (Apple/Google geliştirici hesabı ister).

## Ekranlar

| Sekme / ekran | Ne yapar |
|---|---|
| Giriş / Kayıt | Müşteri davet koduyla, muhasebeci büro adıyla kayıt olur |
| Belgeler | Liste, aşağı çekerek yenileme, durum ve uyarı özeti |
| Belge Yükle | Kamera ile çek, galeriden seç, PDF/XML seç; yükleme sonrası okunan tutar ve durum |
| Belge detayı | Alan bazında güven skoru, uyarılar, silme |
| Yardım | Asistan; yanıtın "ekrana git" düğmesi ilgili sekmeye götürür |
| Hesabım | Bilgiler, çıkış |

İnceleme, düzeltme, onay ve dışa aktarma bilerek mobilde yoktur (web/masaüstü). Asistan mobilde bunları sorana bunu açıkça söyler.

## Güvenlik ve gizlilik

- Oturum jetonu `expo-secure-store` ile iOS Keychain / Android Keystore'da saklanır (web'deki `localStorage`'dan daha güvenli).
- Kamera izni yalnızca fotoğraf çekerken istenir; reddedilirse açıklayıcı uyarı gösterilir.
- Yükleme öncesi 15 MB sınırı istemcide de kontrol edilir; dosya adları temizlenir (`safeFileName`).

## Bilinen sınırlar

- **Bu uygulama gerçek bir telefonda veya emülatörde çalıştırılıp denenmedi.** Yalnızca TypeScript denetimi ve
  `src/logic.ts` birim testleri yapıldı; ekranların görünümü ve kamera/dosya seçici akışları cihazda doğrulanmadı.
- Orijinal belgeyi açma/paylaşma yok. Bildirim yok. Çevrimdışı mod yok. Şifre sıfırlama yok.
- `src/types.ts`, `src/logic.ts` ile web'deki karşılıklarının bir kısmı tekrarlanmıştır; ileride ortak bir pakete taşınabilir.
- Android'de HTTP (şifresiz) adres yalnızca geliştirmede çalışır; üretim derlemesi için HTTPS gerekir.
