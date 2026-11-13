# chatbot

Uygulama içi yardım asistanı. Kullanıcı bir şeyi bulamadığında veya nasıl yapacağını bilmediğinde sorar; asistan
soruyu anlar, cevaplar, adımları anlatır ve istemciye "şu ekrana git" eylemi (`action`) döndürür. Böylece web,
masaüstü ve mobil uygulama kullanıcıyı doğrudan ilgili ekrana götürebilir.

```
POST /chat   {"message": "yükleme butonu nerede", "client": "mobile", "screen": "home"}
→ {
    "answer": "Alt menüdeki “Belge Yükle” sekmesi içinde bulabilirsin. Belge yüklemek için ...",
    "steps": ["“Belge Yükle” ekranını aç.", "Dosyanı seç ...", ...],
    "action": {"type": "navigate", "screen": "upload", "label": "“Belge Yükle” ekranını aç"},
    "suggestions": ["fişin fotoğrafını nasıl çekerim", ...],
    "matched": "upload", "source": "kb", "where": "Alt menüdeki “Belge Yükle” sekmesi"
  }
GET  /chat/topics?client=web      → hızlı soru düğmeleri için örnek sorular
```

`source` değerleri: `kb` (bilgi tabanı), `restricted` (rolün/istemcinin erişemediği özellik, nedeni anlatılır),
`fallback` ("anlayamadım" + öneriler), `smalltalk` (selam/teşekkür), `llm` (isteğe bağlı Claude).

## Nasıl çalışır

1. **Bilgi tabanı** (`knowledge.json`): her özellik için başlık, anahtar kelimeler, örnek sorular, cevap, adımlar,
   ekran kodu, hangi rol/istemcide kullanılabildiği. "Henüz yok" olan özellikler de kayıtlıdır
   (şifre sıfırlama, Logo/Mikro entegrasyonu, kalem okuma), asistan olmayan bir özelliği asla var gibi anlatmaz.
2. **Arama** (`engine.py`): Türkçe normalizasyon (ı/İ, ş, ğ...), kaba kök bulma, sorgu kapsama puanı (IDF ağırlıklı),
   tam sözcük ve ifade eşleşme bonusları. Belirsiz sorularda (iki aday yakınsa) kullanıcıya hangisini kastettiğini sorar.
3. **Rol ve istemci kuralları:** Rol oturumdan gelir, istekten değil (müşteri gövdede rol iddia edemez, testli).
   Müşteri muhasebeci özelliğini sorarsa nedeni anlatılır; mobilde olmayan bir ekran sorulursa web/masaüstüne yönlendirilir.
   `action` yalnızca o istemcide gerçekten var olan ekranlara verilir.
4. **Ekran bağlamı:** "bunu nasıl yaparım" gibi kısa sorular, istemcinin gönderdiği `screen` değerine göre yanıtlanır.
5. **İsteğe bağlı Claude** (`llm.py`, `CHATBOT_MODE=hybrid` + `ANTHROPIC_API_KEY`): yerel eşleşme güvenli değilse
   çağrılır. Claude'a yalnızca soru, rol, istemci türü ve ilgili yardım metinleri gider (belge/fatura verisi gitmez).
   Yalnızca verilen yardım metinlerine dayanır; çıktısı doğrulanır (ekran kodu var mı, istemcide mevcut mu).
   Başarısızlıkta yerel yanıta dönülür.

## Senaryolar ve ölçüm

```bash
python -m pytest -q                 # 81 test (depo kökünde: python -m pytest chatbot -q)
python -m chatbot.eval_heldout -v   # hiç ayarlanmamış sorularla ölçüm
```

- `scenarios.json`: 56 senaryo (nerede/nasıl soruları, rol kısıtı, istemci kısıtı, olmayan özellikler, selam,
  konu dışı, anlamsız metin, prompt enjeksiyonu denemesi, ekran bağlamı). Büyük harf, Türkçe karaktersiz ve
  noktalamalı varyantlarla da test edilir.
- Bunlar bilgi tabanıyla birlikte yazıldığı için **kendi içinde başarı kanıt sayılmaz**.

**Yerel (anahtarsız) modun gerçek başarısı** hiç görmediği ifadelerle ölçüldü (`tests/heldout_c.json`, 25 soru,
motor bu sete göre ayarlanmadı):

| Sonuç | Oran |
|---|---|
| Doğru konuyu buldu | %40 |
| "Anlayamadım" deyip öneri sundu | %52 |
| Yanlış konuyu cevapladı | %8 |

Yorum: kelime tabanlı arama, bilgi tabanındaki sözcüklerden farklı ağızla sorulan sorularda zayıf kalıyor; ama çoğunlukla
yanlış cevap vermek yerine öneri sunuyor (yanlış cevap oranı testle ≤ %12'de tutuluyor). Bu sınır, `hybrid` modun
(Claude) varlık sebebidir. **`hybrid` mod canlı API anahtarıyla denenmedi;** yalnızca sahte istemciyle çağrı koşulları,
çıktı doğrulama ve hata durumunda yerel yanıta dönüş test edildi. Ölçümü yapmadan "hybrid daha iyi" denemez.

Not: `heldout_a.json` geliştirme seti, `heldout_b.json` bilgi tabanı genişletilirken dolaylı olarak sızdığı için
tarafsız değil; ikisi de yalnızca geçmişi göstermek için duruyor.

## API'ye bağlama

`api/app/main.py`, kök dizinde `chatbot/` varsa yönlendiriciyi otomatik bağlar: `build_router(get_current_user)`.
Kimlik doğrulama ve rol API'nin oturumundan gelir. Kullanıcı başına dakikada 30 mesaj sınırı vardır.

## Bilgi tabanına konu ekleme

`knowledge.json` içine yeni bir kayıt ekle (`id`, `title`, `screen`, `roles`, `clients`, `keywords`, `examples`, `answer`,
`steps`), ardından `scenarios.json`'a o kaydı hedefleyen 2-3 senaryo yaz. Anahtar kelimeleri Türkçe karaktersiz
ve küçük harfle yaz. Gerçek kullanıcıların kullandığı sözcükleri (eş anlamlılar, fiil çekimleri) eklemek başarıyı en çok artıran şeydir.
