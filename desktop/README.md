# desktop

Masaüstü uygulaması (Electron). `web/` arayüzünün aynı derlemesini sarmalar; tek fark pencere, menü ve sıkı güvenlik ayarlarıdır.
Web ve masaüstü aynı hesapla giriş yapar, belgeler ortak görünür (veri API'de).

## Çalıştırma

```bash
cd ../web && npm install && npm run build    # önce web'i derle (API adresi: VITE_API_URL, varsayılan http://localhost:8000)
cd ../desktop && npm install
npm start                                     # web/dist -> app/ kopyalar ve açar
npm test                                      # güvenlik politikası testleri
npm run dist                                  # yükleyici üretir (Windows: nsis, macOS: dmg, Linux: AppImage)
```

Masaüstü sürümünü farklı bir sunucuya bağlamak için web'i derlerken adresi ver:
`VITE_API_URL=https://api.ornek.com npm run build` (Windows PowerShell: `$env:VITE_API_URL="https://api.ornek.com"; npm run build`).

## Güvenlik

- `contextIsolation`, `sandbox`, `nodeIntegration: false`; sayfaya Node erişimi yok. Preload yalnızca `{platform}` açar.
- Pencere yalnızca kendi `app/` dosyalarına gezinebilir (komşu klasör taklidi dahil engellenir, testli).
- `window.open`: `blob:` (belge önizleme) kısıtlı pencerede açılır, `https:` sistem tarayıcısına gider, geri kalanı reddedilir.
- Tarayıcı izinleri (kamera, konum, bildirim) tümüyle reddedilir; masaüstünde dosya seçici kullanılır.
- Tek örnek kilidi: uygulama ikinci kez açılırsa mevcut pencere öne gelir.

## Doğrulandı

Gerçek Electron 33 penceresinde (Windows) denendi: uygulama `file://` ile açılır, sayfada `require`/`process` yoktur,
`https://` adresine gezinme engellenir, ve pencere API'ye JSON gövdeli giriş isteği atabilir (HTTP 200). Electron `file://`
sayfaları için CORS'u bu sürümde engellemiyor; farklı bir sürümde sorun çıkarsa `app://` özel protokolüne geçilip
`CORS_ORIGINS`'e eklenmelidir.

## Bilinen sınırlar

- Yükleyici (`npm run dist`) bu ortamda üretilmedi/denenmedi; kod imzalama ve otomatik güncelleme yok
  (imzasız uygulamalar Windows SmartScreen ve macOS Gatekeeper uyarısı verir).
- Telefon kamerası yalnızca web (PWA) ve mobil uygulamada vardır.
