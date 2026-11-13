import type { ChatReply, ClientKind, Doc, InvoiceData, Org, TokenOut, User } from "./types";

const BASE: string = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";
const TOKEN_KEY = "fatura_token";

// Not: Bearer token localStorage'da tutulur. XSS'e karşı CSP (index.html) ve React'in otomatik kaçışı kullanılır;
// yüksek güvenlik gereken kurulumlarda httpOnly çerez + CSRF korumasına geçilmelidir.
let token: string | null = safeGet();

function safeGet(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(value: string | null): void {
  token = value;
  try {
    if (value) localStorage.setItem(TOKEN_KEY, value);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* gizli sekme vb.: bellekte kalır */
  }
}

export const hasToken = (): boolean => token !== null;

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public payload?: unknown,
  ) {
    super(message);
  }
}

/** FastAPI hata gövdesinden okunabilir bir mesaj çıkarır. */
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

let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(fn: () => void): void {
  onUnauthorized = fn;
}

async function raw(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "Sunucuya ulaşılamadı. İnternet bağlantını kontrol et.");
  }
  if (res.status === 401 && token && !path.startsWith("/auth/login")) {
    setToken(null);
    onUnauthorized?.();
  }
  return res;
}

async function json<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await raw(path, init);
  const payload = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, errorMessage(payload, `Hata (${res.status})`), payload);
  return payload as T;
}

const jsonBody = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export interface RegisterInput {
  email: string;
  password: string;
  full_name: string;
  role: "accountant" | "client";
  org_name?: string;
  invite_code?: string;
}

export const api = {
  register: (b: RegisterInput) => json<TokenOut>("/auth/register", jsonBody("POST", b)),
  login: (email: string, password: string) => json<TokenOut>("/auth/login", jsonBody("POST", { email, password })),
  me: () => json<User>("/auth/me"),
  org: () => json<Org>("/auth/org"),

  listDocs: (params: { status?: string; q?: string; limit?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.status) qs.set("status", params.status);
    if (params.q) qs.set("q", params.q);
    qs.set("limit", String(params.limit ?? 100));
    return json<Doc[]>(`/documents?${qs}`);
  },
  getDoc: (id: number) => json<Doc>(`/documents/${id}`),
  patchDoc: (id: number, body: { data?: InvoiceData; status?: "approved" | "rejected" | "needs_review" }) =>
    json<Doc>(`/documents/${id}`, jsonBody("PATCH", body)),
  deleteDoc: async (id: number) => {
    const res = await raw(`/documents/${id}`, { method: "DELETE" });
    if (!res.ok) {
      const payload = await res.json().catch(() => null);
      throw new ApiError(res.status, errorMessage(payload, `Hata (${res.status})`), payload);
    }
  },
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return json<Doc>("/documents", { method: "POST", body: form });
  },

  /** Kimlik doğrulama gerektiren dosyaları blob olarak indirir. */
  blob: async (path: string): Promise<Blob> => {
    const res = await raw(path);
    if (!res.ok) {
      const payload = await res.json().catch(() => null);
      throw new ApiError(res.status, errorMessage(payload, `Hata (${res.status})`), payload);
    }
    return res.blob();
  },

  chat: (message: string, client: ClientKind, screen?: string) =>
    json<ChatReply>("/chat", jsonBody("POST", { message, client, screen })),
  chatTopics: (client: ClientKind) => json<string[]>(`/chat/topics?client=${client}`),
};

/** Blob'u kullanıcıya indirtir. */
export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}

/** Blob'u yeni sekmede açar (PDF/görsel önizleme). */
export function openBlob(blob: Blob): void {
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank", "noopener");
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
