// Saf (React Native'den bağımsız) yardımcılar: birim testleri vitest ile çalışır.

export type DocStatus = "uploaded" | "processed" | "needs_review" | "approved" | "rejected" | "failed";

export const STATUS_LABELS: Record<DocStatus, string> = {
  uploaded: "Yüklendi",
  processed: "İşlendi",
  needs_review: "İncelemede",
  approved: "Onaylandı",
  rejected: "Reddedildi",
  failed: "Başarısız",
};

export const FIELD_LABELS: Record<string, string> = {
  seller_name: "Satıcı unvanı",
  seller_vkn: "Satıcı VKN/TCKN",
  buyer_name: "Alıcı unvanı",
  buyer_vkn: "Alıcı VKN/TCKN",
  invoice_no: "Fatura / fiş no",
  invoice_date: "Tarih",
  currency: "Para birimi",
  subtotal: "Matrah (KDV hariç)",
  vat_rate: "KDV oranı (%)",
  vat_amount: "KDV tutarı",
  total: "Genel toplam",
};

export function formatAmount(value: number | null | undefined, currency: string | null | undefined = "TRY"): string {
  if (value === null || value === undefined) return "-";
  // Hermes'te Intl.NumberFormat eksik olabilir; kendimiz biçimlendirelim: 1.234,56
  const [int, dec] = value.toFixed(2).split(".");
  const grouped = int.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const symbol = currency === "TRY" || !currency ? "₺" : currency === "USD" ? "$" : currency === "EUR" ? "€" : currency;
  return `${symbol}${grouped},${dec}`;
}

/** '2025-03-12' -> '12.03.2025' */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "-";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  return m ? `${m[3]}.${m[2]}.${m[1]}` : iso;
}

export function confidenceLevel(c: number | undefined): "high" | "mid" | "low" | "none" {
  if (c === undefined) return "none";
  if (c >= 0.85) return "high";
  if (c >= 0.7) return "mid";
  return "low";
}

/** FastAPI hata gövdesinden okunabilir mesaj çıkarır. */
export function errorMessage(payload: unknown, fallback: string): string {
  const detail = (payload as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string; loc?: unknown[] };
    const field = Array.isArray(first.loc) ? String(first.loc[first.loc.length - 1]) : "";
    return first.msg ? `${field ? field + ": " : ""}${first.msg}` : fallback;
  }
  return fallback;
}

export type TabName = "Documents" | "Upload" | "Assistant" | "Profile";

/**
 * Chatbot'un döndürdüğü ekran kodlarını mobil sekmelere çevirir.
 * Mobilde olmayan ekranlar (inceleme, dışa aktarma, ekip) null döner; chatbot zaten bunlar için eylem vermez.
 */
export function tabForScreen(screen: string): TabName | null {
  switch (screen) {
    case "home":
    case "documents":
      return "Documents";
    case "upload":
      return "Upload";
    case "profile":
      return "Profile";
    case "help":
      return "Assistant";
    default:
      return null;
  }
}

/** Dosya adından MIME türü (kamera/galeri/dosya seçici bazen tür vermez). */
export function guessMime(name: string, fallback = "application/octet-stream"): string {
  const ext = name.toLowerCase().split(".").pop() ?? "";
  const map: Record<string, string> = {
    pdf: "application/pdf",
    xml: "application/xml",
    png: "image/png",
    jpg: "image/jpeg",
    jpeg: "image/jpeg",
    webp: "image/webp",
  };
  return map[ext] ?? fallback;
}

/** Yükleme için uygun, güvenli bir dosya adı üretir (uzantıyı korur). */
export function safeFileName(name: string | null | undefined, mime: string): string {
  const extFromMime: Record<string, string> = {
    "application/pdf": "pdf",
    "application/xml": "xml",
    "text/xml": "xml",
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
  };
  const cleaned = (name ?? "")
    .replace(/[^\w.\-]+/g, "_") // yol ayracı ve özel karakterleri at
    .replace(/\.{2,}/g, ".") // ".." dizilerini tekle
    .replace(/^[._]+/, ""); // baştaki nokta/alt çizgileri kırp
  if (/\.(pdf|xml|png|jpe?g|webp)$/i.test(cleaned)) return cleaned;
  return `${cleaned || "belge"}.${extFromMime[mime] ?? "jpg"}`;
}
