import type { DocStatus, InvoiceData } from "./types";

export const STATUS_LABELS: Record<DocStatus, string> = {
  uploaded: "Yüklendi",
  processed: "İşlendi",
  needs_review: "İncelemede",
  approved: "Onaylandı",
  rejected: "Reddedildi",
  failed: "Başarısız",
};

export const FIELD_LABELS: Record<keyof InvoiceData, string> = {
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

export const FIELD_ORDER = Object.keys(FIELD_LABELS) as (keyof InvoiceData)[];
export const NUMERIC_FIELDS: ReadonlySet<string> = new Set(["subtotal", "vat_rate", "vat_amount", "total"]);

export function formatAmount(value: number | null | undefined, currency: string | null | undefined = "TRY"): string {
  if (value === null || value === undefined) return "-";
  try {
    return new Intl.NumberFormat("tr-TR", { style: "currency", currency: currency || "TRY" }).format(value);
  } catch {
    return `${value.toFixed(2)} ${currency ?? ""}`.trim();
  }
}

/** '2025-03-12' -> '12.03.2025' */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "-";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  return m ? `${m[3]}.${m[2]}.${m[1]}` : iso;
}

export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString("tr-TR", { dateStyle: "short", timeStyle: "short" });
}

export function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

/** Güven skoruna göre seviye: arayüzde renk ve metin için. */
export function confidenceLevel(c: number | undefined): "high" | "mid" | "low" | "none" {
  if (c === undefined) return "none";
  if (c >= 0.85) return "high";
  if (c >= 0.7) return "mid";
  return "low";
}

/** Düzenleme formundaki metni API'nin beklediği türe çevirir; boş metin null olur. */
export function parseFieldInput(field: string, text: string): string | number | null {
  const t = text.trim();
  if (t === "") return null;
  if (NUMERIC_FIELDS.has(field)) {
    // "1.234,56" -> 1234.56 ; "1234.56" -> 1234.56
    const normalized = t.includes(",") ? t.replace(/\./g, "").replace(",", ".") : t;
    const n = Number(normalized);
    return Number.isFinite(n) ? n : null;
  }
  return t;
}
