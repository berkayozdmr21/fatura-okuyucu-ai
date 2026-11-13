import type { DocStatus } from "./logic";

export type Role = "accountant" | "client";

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

export interface Issue {
  code: string;
  field: string | null;
  severity: "error" | "warning";
  message: string;
}

export interface Doc {
  id: number;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  status: DocStatus;
  extractor: string | null;
  data: Record<string, string | number | null | undefined>;
  field_confidence: Record<string, number>;
  issues: Issue[];
  needs_review: boolean;
  has_file: boolean;
  created_at: string;
  expires_at: string | null;
}

export interface ChatReply {
  answer: string;
  steps: string[];
  action: { type: "navigate"; screen: string; label: string } | null;
  suggestions: string[];
  matched: string | null;
  source: string;
  where: string | null;
}

export interface UploadFile {
  uri: string;
  name: string;
  mimeType: string;
}
