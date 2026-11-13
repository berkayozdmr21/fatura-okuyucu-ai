# web

Web arayüzü: React + TypeScript + Vite. Hem tarayıcıda hem (aynı derleme) masaüstü uygulamasında çalışır;
telefonda "ana ekrana ekle" ile PWA olarak kurulur ve kamerayla fiş çekebilir.

## Çalıştırma

```bash
cd web
npm install
npm run dev            # http://localhost:5173  (API: http://localhost:8000)
npm test               # birim testleri
npm run build          # dist/ (masaüstü uygulaması bu klasörü kullanır)
```

API adresi `VITE_API_URL` ile değiştirilir (varsayılan `http://localhost:8000`). Bu bir gizli bilgi değildir;
gizli anahtarlar istemciye asla konmaz.

## Ekranlar

| Ekran | Kim | Ne yapar |
|---|---|---|
| Giriş / Kayıt | herkes | Muhasebeci büro adıyla, müşteri davet koduyla kayıt olur |
| Ana Sayfa | giriş yapmış | Özet sayılar, son belgeler |
| Belge Yükle | giriş yapmış | Sürükle-bırak, çoklu dosya, telefonda "Fotoğraf çek" (kamera) |
| Belgeler | giriş yapmış | Durum filtresi, dosya adı arama |
| Belge Detayı | giriş yapmış | Alan bazında güven skoru, uyarılar; muhasebeci düzeltir/onaylar/reddeder |
| İnceleme Bekleyenler | muhasebeci | `needs_review` filtreli belge listesi |
| Dışa Aktar | muhasebeci | Excel/CSV indirme |
| Büro ve Davet Kodu | muhasebeci | Müşteri davet kodu |
| Yardım asistanı | giriş yapmış | Sağ alt köşe; soruyu yanıtlar, ilgili ekrana götürür |

## Tasarım notları

- **`HashRouter`:** Electron `file://` ile yüklediği için kullanıldı; web'de de sorunsuz çalışır.
- **Telefonda** kenar menü alt sekmeye dönüşür; dokunma hedefleri en az 44 px; açık/koyu tema `prefers-color-scheme` ile.
- **Erişilebilirlik:** form etiketleri, `aria-live` sohbet alanı, odak halkası, güven göstergesi yalnızca renge bağlı değil (metin de var).
- **Güvenlik:** React metinleri otomatik kaçırır (`dangerouslySetInnerHTML` yok); `index.html` içinde sıkı CSP vardır.
  Oturum jetonu `localStorage`'da tutulur; XSS'e karşı CSP'ye güveniyoruz. Yüksek güvenlik gerektiren kurulumda
  `httpOnly` çerez + CSRF koruması daha uygundur.
- **PWA:** servis çalışanı yalnızca uygulama kabuğunu önbelleğe alır. API yanıtları ve belge dosyaları **asla** önbelleğe alınmaz.
- **Asistan eylemleri:** sohbet yanıtındaki `action.screen` kodu `src/screens.ts` ile rotaya çevrilir; bilinmeyen kod yok sayılır.

## Bilinen sınırlar

- Tarayıcıda otomatik arayüz testi (Playwright vb.) yok; yalnızca saf fonksiyonlar birim testli, arayüz elle doğrulandı.
- Çevrimdışı çalışma yok: PWA kabuğu açılır ama veri için sunucu gerekir.
- Şifre sıfırlama/değiştirme ekranı yok (API'de de yok).
