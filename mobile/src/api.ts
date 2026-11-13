import * as SecureStore from "expo-secure-store";

import { API_URL } from "./config";
import { errorMessage } from "./logic";
import type { ChatReply, Doc, TokenOut, UploadFile, User } from "./types";

const TOKEN_KEY = "fatura_token";

// Oturum jetonu işletim sisteminin güvenli deposunda (iOS Keychain / Android Keystore) tutulur.
let token: string | null = null;

export async function loadToken(): Promise<string | null> {
  try {
    token = await SecureStore.getItemAsync(TOKEN_KEY);
  } catch {
    token = null;
  }
  return token;
}

export async function setToken(value: string | null): Promise<void> {
  token = value;
  try {
    if (value) await SecureStore.setItemAsync(TOKEN_KEY, value);
    else await SecureStore.deleteItemAsync(TOKEN_KEY);
  } catch {
    /* depo kullanılamıyorsa jeton yalnızca bellekte kalır */
  }
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public payload?: unknown,
  ) {
    super(message);
  }
}

let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(fn: () => void): void {
  onUnauthorized = fn;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { ...(init.headers as Record<string, string> | undefined) };
  if (token) headers.Authorization = `Bearer ${token}`;
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "Sunucuya ulaşılamadı. İnternet bağlantını kontrol et.");
  }
  if (res.status === 204) return undefined as T;
  const payload = await res.json().catch(() => null);
  if (res.status === 401 && token && !path.startsWith("/auth/login")) {
    await setToken(null);
    onUnauthorized?.();
  }
  if (!res.ok) throw new ApiError(res.status, errorMessage(payload, `Hata (${res.status})`), payload);
  return payload as T;
}

const jsonInit = (method: string, body: unknown): RequestInit => ({
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
  login: (email: string, password: string) => request<TokenOut>("/auth/login", jsonInit("POST", { email, password })),
  register: (b: RegisterInput) => request<TokenOut>("/auth/register", jsonInit("POST", b)),
  me: () => request<User>("/auth/me"),
  listDocs: (status?: string) =>
    request<Doc[]>(`/documents?limit=100${status ? `&status=${encodeURIComponent(status)}` : ""}`),
  getDoc: (id: number) => request<Doc>(`/documents/${id}`),
  deleteDoc: (id: number) => request<void>(`/documents/${id}`, { method: "DELETE" }),
  upload: (file: UploadFile) => {
    const form = new FormData();
    // React Native FormData dosyayı { uri, name, type } nesnesiyle alır
    form.append("file", { uri: file.uri, name: file.name, type: file.mimeType } as unknown as Blob);
    return request<Doc>("/documents", { method: "POST", body: form });
  },
  chat: (message: string, screen?: string) =>
    request<ChatReply>("/chat", jsonInit("POST", { message, client: "mobile", screen })),
  chatTopics: () => request<string[]>("/chat/topics?client=mobile"),
};
