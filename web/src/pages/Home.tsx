import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api";
import { useAuth } from "../auth";
import { StatusBadge } from "../components/Badges";
import { formatAmount, formatDateTime } from "../format";
import type { Doc } from "../types";

export default function Home() {
  const { user } = useAuth();
  const [docs, setDocs] = useState<Doc[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listDocs({ limit: 200 }).then(setDocs).catch((e: Error) => setError(e.message));
  }, []);

  const count = (s: string) => docs?.filter((d) => d.status === s).length ?? 0;
  const accountant = user?.role === "accountant";

  return (
    <>
      <h1>Merhaba, {user?.full_name.split(" ")[0]}</h1>
      {error && <p className="error">{error}</p>}
      <div className="stats">
        <Link className="card stat" to="/documents">
          <strong>{docs?.length ?? "…"}</strong>
          <span>Toplam belge</span>
        </Link>
        <Link className="card stat warn" to="/documents?status=needs_review">
          <strong>{docs ? count("needs_review") : "…"}</strong>
          <span>{accountant ? "İnceleme bekliyor" : "Muhasebeci kontrolünde"}</span>
        </Link>
        <Link className="card stat ok" to="/documents?status=approved">
          <strong>{docs ? count("approved") : "…"}</strong>
          <span>Onaylandı</span>
        </Link>
      </div>

      <div className="row">
        <Link className="btn" to="/upload">
          Belge yükle
        </Link>
      </div>

      <h2>Son belgeler</h2>
      {docs && docs.length === 0 && <p className="muted">Henüz belge yok. İlk faturanı veya fişini yükleyerek başla.</p>}
      <ul className="doc-list">
        {docs?.slice(0, 5).map((d) => (
          <li key={d.id}>
            <Link to={`/documents/${d.id}`} className="card doc-row">
              <div>
                <strong>{d.data.seller_name ?? d.original_filename}</strong>
                <small>{formatDateTime(d.created_at)}</small>
              </div>
              <div className="doc-meta">
                <span>{formatAmount(d.data.total, d.data.currency)}</span>
                <StatusBadge status={d.status} />
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}
