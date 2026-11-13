import type { ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";

import { useAuth } from "../auth";
import { navFor } from "../screens";
import Chat from "./Chat";

export default function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  if (!user) return null;

  const items = navFor(user.role);
  // "İnceleme Bekleyenler" ile "Belgeler" aynı yolda; query'ye bakarak doğru olanı aktif göster
  const isActive = (to: string): boolean => {
    const [path, query] = to.split("?");
    if (location.pathname !== path && !(path !== "/" && location.pathname.startsWith(path + "/"))) return false;
    const wantsReview = query?.includes("status=needs_review") ?? false;
    const hasReview = location.search.includes("status=needs_review");
    return path === "/documents" ? wantsReview === hasReview : true;
  };

  return (
    <div className="shell">
      <aside className="sidebar" aria-label="Ana menü">
        <div className="brand">
          <img src="./icon.svg" alt="" width={32} height={32} />
          <span>Fatura Okuyucu</span>
        </div>
        <nav>
          {items.map((i) => (
            <NavLink key={i.to} to={i.to} className={isActive(i.to) ? "active" : ""} end={i.to === "/"}>
              {i.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="who">
            <strong>{user.full_name}</strong>
            <small>
              {user.role === "accountant" ? "Muhasebeci" : "Müşteri"} · {user.org_name}
            </small>
          </div>
          <button className="btn ghost" onClick={logout}>
            Çıkış yap
          </button>
        </div>
      </aside>
      <main className="content" id="main">
        {children}
      </main>
      <Chat />
    </div>
  );
}
