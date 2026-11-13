import type { Role } from "./types";

/** Chatbot'un döndürdüğü ekran kodları -> uygulama içi rota. (chatbot/knowledge.json "screens" ile aynı kodlar) */
export const SCREEN_ROUTES: Record<string, string> = {
  home: "/",
  upload: "/upload",
  documents: "/documents",
  review: "/documents?status=needs_review",
  export: "/export",
  team: "/team",
  profile: "/profile",
  help: "/help",
};

export function routeForScreen(screen: string): string | null {
  return SCREEN_ROUTES[screen] ?? null;
}

export interface NavItem {
  to: string;
  label: string;
  roles: Role[];
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Ana Sayfa", roles: ["client", "accountant"] },
  { to: "/upload", label: "Belge Yükle", roles: ["client", "accountant"] },
  { to: "/documents", label: "Belgeler", roles: ["client", "accountant"] },
  { to: "/documents?status=needs_review", label: "İnceleme Bekleyenler", roles: ["accountant"] },
  { to: "/export", label: "Dışa Aktar", roles: ["accountant"] },
  { to: "/team", label: "Büro ve Davet Kodu", roles: ["accountant"] },
  { to: "/profile", label: "Hesabım", roles: ["client", "accountant"] },
  { to: "/help", label: "Yardım", roles: ["client", "accountant"] },
];

export const navFor = (role: Role): NavItem[] => NAV_ITEMS.filter((i) => i.roles.includes(role));
