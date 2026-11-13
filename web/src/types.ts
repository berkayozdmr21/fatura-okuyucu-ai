export type Role = "accountant" | "client";
export type ClientKind = "web" | "desktop" | "mobile";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  org_id: number;
  org_name: string;
}

export interface TokenOut {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Org {
  id: number;
  name: string;
  invite_code: string | null;
}

export type DocStatus = "uploaded" | "processed" | "needs_review" | "approved" | "rejected" | "failed";

export interface Issue {
  code: string;
  field: string | null;
  severity: "error" | "warning";
  message: string;
}

export type InvoiceData = Partial<{
  seller_name: string | null;
  seller_vkn: string | null;
  buyer_name: string | null;
  buyer_vkn: string | null;
  invoice_no: string | null;
  invoice_date: string | null;
  currency: string | null;
  subtotal: number | null;
  vat_rate: number | null;
  vat_amount: number | null;
  total: number | null;
}>;

export interface Doc {
  id: number;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  status: DocStatus;
  extractor: string | null;
  data: InvoiceData;
  field_confidence: Record<string, number>;
  issues: Issue[];
  needs_review: boolean;
  has_file: boolean;
  uploader_id: number;
  created_at: string;
  expires_at: string | null;
}

export interface ChatAction {
  type: "navigate";
  screen: string;
  label: string;
}

export interface ChatReply {
  answer: string;
  steps: string[];
  action: ChatAction | null;
  suggestions: string[];
  matched: string | null;
  confidence: number;
  source: string;
  where: string | null;
}
