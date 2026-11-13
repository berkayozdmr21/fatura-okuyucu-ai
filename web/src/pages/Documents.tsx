import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { api } from "../api";
import { StatusBadge } from "../components/Badges";
import { formatAmount, formatDate, formatDateTime, STATUS_LABELS } from "../format";
import type { Doc } from "../types";

export default function Documents() {
  const [params, setParams] = useSearchParams();
  const status = params.get("status") ?? "";
  const [q, setQ] = useState("");
  const [docs, setDocs] = useState<Doc[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDocs(null);
    const handle = setTimeout(() => {
      api
        .listDocs({ status: status || undefined, q: q.trim() || undefined })
        .then(setDocs)
        .catch((e: Error) => setError(e.message));
    }, 200); // yazarken her tuşta istek atma
    return () => clearTimeout(handle);
  }, [status, q]);

  const title = status === "needs_review" ? "İnceleme bekleyenler" : "Belgeler";

  return (
    <>
      <h1>{title}</h1>
      <div className="filters">
        <label className="sr-only" htmlFor="q">
          Dosya adında ara
        </label>
        <input id="q" type="search" placeholder="Dosya adında ara…" value={q} onChange={(e) => setQ(e.target.value)} />
        <label className="sr-only" htmlFor="status">
          Durum
        </label>
        <select
          id="status"
          value={status}
          onChange={(e) => (e.target.value ? setParams({ status: e.target.value }) : setParams({}))}
        >
          <option value="">Tüm durumlar</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="error">{error}</p>}
      {docs === null && !error && <p className="muted">Yükleniyor…</p>}
      {docs?.length === 0 && <p className="muted">Bu filtreyle eşleşen belge yok.</p>}
      <ul className="doc-list">
        {docs?.map((d) => (
          <li key={d.id}>
            <Link to={`/documents/${d.id}`} className="card doc-row">
              <div>
                <strong>{d.data.seller_name ?? d.original_filename}</strong>
                <small>
                  {d.data.invoice_no ?? "no yok"} · {formatDate(d.data.invoice_date)} · yüklendi {formatDateTime(d.created_at)}
                </small>
                {d.issues.length > 0 && (
                  <small className="warn-text">
                    {d.issues.filter((i) => i.severity === "error").length > 0 ? "⚠ " : "• "}
                    {d.issues[0].message}
                  </small>
                )}
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
