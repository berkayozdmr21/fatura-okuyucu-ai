# Fatura Okuyucu

Muhasebe büroları ve müşterileri için fatura/fiş okuyup yapılandırılmış veriye çeviren, çok istemcili (web, masaüstü, mobil) bir sistem.

> Bu README proje ilerledikçe güncellenir. Bitmiş hali `main` branch'inde.

## Bileşenler

| Klasör | Açıklama | Branch |
|---|---|---|
| `database/` | PostgreSQL şeması, docker-compose, demo veri | `database` |
| `api/` | FastAPI arka uç: kimlik, belge çıkarımı, doğrulama, dışa aktarım | `api` |
| `chatbot/` | Uygulama içi yardım asistanı (nerede ne var, nasıl kullanılır) | `chatbot` |
| `web/` | Web arayüzü (PWA, telefonda kamerayla fiş çekme) | `web` |
| `desktop/` | Masaüstü uygulaması (Electron) | `desktop` |
| `mobile/` | Mobil uygulama (Expo / React Native) | `mobile` |

Her bileşen kendi branch'inde geliştirildi, tamamlanınca `main`'de birleştirildi.

## Gizli bilgiler

Anahtarlar, şifreler ve veritabanı bilgileri **repoda yoktur**. `.env.example` dosyasını `.env` olarak kopyalayıp kendi değerlerini yaz. `.env` dosyası `.gitignore` ile dışarıda tutulur.
