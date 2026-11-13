"use strict";
// Pencere/gezinme güvenlik politikası. Saf fonksiyonlar: Electron olmadan test edilebilir.

/** Uygulamanın kendi dosyaları: file:///.../app/... */
function isAppUrl(url, appDirUrl) {
  // Sondaki "/" zorunlu: ".../app" öneki ".../app-evil/..." klasörünü de kabul etmesin
  const prefix = appDirUrl.endsWith("/") ? appDirUrl : `${appDirUrl}/`;
  try {
    return new URL(url).protocol === "file:" && url.startsWith(prefix);
  } catch {
    return false;
  }
}

/** Uygulama penceresi kendi dosyaları dışına gezinemez (kimlik avı / uzaktan kod yükleme riskini keser). */
function isNavigationAllowed(url, appDirUrl) {
  return isAppUrl(url, appDirUrl);
}

/**
 * window.open / target=_blank isteklerinin ne yapacağı:
 *  - "popup"    : blob: (uygulamanın ürettiği PDF/görsel önizleme) -> kısıtlı yeni pencere
 *  - "external" : https: bağlantı -> sistem tarayıcısında aç
 *  - "deny"     : geri kalan her şey (file:, http:, javascript:, data: ...)
 */
function classifyOpen(url) {
  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    return "deny";
  }
  if (parsed.protocol === "blob:") return "popup";
  if (parsed.protocol === "https:") return "external";
  return "deny";
}

/** Sayfanın hiçbir tarayıcı iznine (kamera, konum, bildirim...) ihtiyacı yok; hepsi reddedilir. */
function isPermissionAllowed() {
  return false;
}

module.exports = { isAppUrl, isNavigationAllowed, classifyOpen, isPermissionAllowed };
