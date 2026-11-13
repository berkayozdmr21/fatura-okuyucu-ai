import { useState } from "react";

import { api, ApiError, saveBlob } from "../api";
import { STATUS_LABELS } from "../format";

export default function Export() {
  const [status, setStatus] = useState("approved");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function download(format: "xlsx" | "csv") {
    setBusy(format);
    setError(null);
    try {
      const blob = await api.blob(`/exports/documents.${format}?status=${encodeURIComponent(status)}`);
      saveBlob(blob, `faturalar.${format}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "İndirilemedi.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <h1>Dışa aktar</h1>
      <section className="card">
        <p>
          Seçtiğin durumdaki belgeler tablo olarak indirilir. Muhasebe programına aktarmadan önce yalnızca{" "}
          <strong>onaylanmış</strong> belgeleri almanı öneririz.
        </p>
        <label className="field">
          <span>Hangi belgeler?</span>
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            {Object.entries(STATUS_LABELS).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </label>
        <div className="row">
          <button className="btn" onClick={() => download("xlsx")} disabled={busy !== null}>
            {busy === "xlsx" ? "Hazırlanıyor…" : "Excel (.xlsx)"}
          </button>
          <button className="btn secondary" onClick={() => download("csv")} disabled={busy !== null}>
            {busy === "csv" ? "Hazırlanıyor…" : "CSV"}
          </button>
        </div>
        {error && <p className="error">{error}</p>}
        <p className="muted">
          Not: Çıktı genel bir tablodur. Logo, Mikro veya Luca için özel içe aktarma şablonu henüz yoktur. CSV dosyası Türkçe
          Excel için noktalı virgülle ayrılır.
        </p>
      </section>
    </>
  );
}
