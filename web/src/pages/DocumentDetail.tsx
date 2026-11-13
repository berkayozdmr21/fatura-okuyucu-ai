import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { api, ApiError, openBlob } from "../api";
import { useAuth } from "../auth";
import { Confidence, StatusBadge } from "../components/Badges";
import { FIELD_LABELS, FIELD_ORDER, formatDateTime, parseFieldInput } from "../format";
import type { Doc, InvoiceData } from "../types";

function toInput(value: unknown): string {
  return value === null || value === undefined ? "" : String(value);
}

export default function DocumentDetail() {
  const { id } = useParams();
  const docId = Number(id);
  const { user } = useAuth();
  const navigate = useNavigate();
  const [doc, setDoc] = useState<Doc | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const accountant = user?.role === "accountant";

  function load(d: Doc) {
    setDoc(d);
    setForm(Object.fromEntries(FIELD_ORDER.map((f) => [f, toInput(d.data[f])])));
  }

  useEffect(() => {
    if (!Number.isInteger(docId)) return;
    api.getDoc(docId).then(load).catch((e: Error) => setError(e.message));
  }, [docId]);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await action();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "İşlem başarısız.");
    } finally {
      setBusy(false);
    }
  }

  async function save(e: FormEvent) {
    e.preventDefault();
    if (!doc) return;
    // Yalnızca değişen alanları gönder
    const changed: InvoiceData = {};
    for (const f of FIELD_ORDER) {
      if (form[f] !== toInput(doc.data[f])) {
        (changed as Record<string, unknown>)[f] = parseFieldInput(f, form[f] ?? "");
      }
    }
    if (Object.keys(changed).length === 0) {
      setMessage("Değişiklik yok.");
      return;
    }
    await run(async () => {
      load(await api.patchDoc(doc.id, { data: changed }));
      setMessage("Kaydedildi, kurallar yeniden kontrol edildi.");
    });
  }

  const setStatus = (status: "approved" | "rejected" | "needs_review") =>
    run(async () => {
      if (doc) load(await api.patchDoc(doc.id, { status }));
    });

  const openFile = () =>
    run(async () => {
      if (doc) openBlob(await api.blob(`/documents/${doc.id}/file`));
    });

  const remove = () => {
    if (!doc || !window.confirm("Bu belge ve dosyası kalıcı olarak silinecek. Emin misin?")) return;
    void run(async () => {
      await api.deleteDoc(doc.id);
      navigate("/documents");
    });
  };

  if (error && !doc) return <p className="error">{error}</p>;
  if (!doc) return <p className="muted">Yükleniyor…</p>;

  const locked = !accountant;
  const errors = doc.issues.filter((i) => i.severity === "error");
  const warnings = doc.issues.filter((i) => i.severity === "warning");

  return (
    <>
      <h1>{doc.data.seller_name ?? doc.original_filename}</h1>
      <p className="row">
        <StatusBadge status={doc.status} />
        <span className="muted">
          {doc.original_filename} · yüklendi {formatDateTime(doc.created_at)} · okuyucu: {doc.extractor ?? "-"}
        </span>
      </p>

      {doc.issues.length > 0 && (
        <section className="card issues" aria-label="Uyarılar">
          <h2>Uyarılar</h2>
          <ul>
            {errors.map((i, k) => (
              <li key={`e${k}`} className="issue-error">
                <strong>Hata:</strong> {i.message}
              </li>
            ))}
            {warnings.map((i, k) => (
              <li key={`w${k}`} className="issue-warning">
                <strong>Uyarı:</strong> {i.message}
              </li>
            ))}
          </ul>
          {!accountant && <p className="muted">Düzeltmeyi bürondaki muhasebeci yapar.</p>}
        </section>
      )}

      <form className="card" onSubmit={save}>
        <h2>Okunan bilgiler</h2>
        <div className="fields">
          {FIELD_ORDER.map((f) => (
            <label key={f} className="field">
              <span>
                {FIELD_LABELS[f]} <Confidence value={doc.field_confidence[f]} />
              </span>
              <input
                value={form[f] ?? ""}
                onChange={(e) => setForm({ ...form, [f]: e.target.value })}
                disabled={locked}
                inputMode={["subtotal", "vat_rate", "vat_amount", "total"].includes(f) ? "decimal" : undefined}
              />
            </label>
          ))}
        </div>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {message && <p className="ok-text">{message}</p>}
        <div className="row">
          {accountant && (
            <>
              <button className="btn" type="submit" disabled={busy}>
                Kaydet
              </button>
              <button className="btn success" type="button" disabled={busy || doc.status === "approved"} onClick={() => setStatus("approved")}>
                Onayla
              </button>
              <button className="btn danger" type="button" disabled={busy || doc.status === "rejected"} onClick={() => setStatus("rejected")}>
                Reddet
              </button>
            </>
          )}
          {doc.has_file ? (
            <button className="btn secondary" type="button" onClick={openFile} disabled={busy}>
              Orijinali aç
            </button>
          ) : (
            <span className="muted">Dosya saklama süresi dolduğu için silindi.</span>
          )}
          {(accountant || doc.status !== "approved") && (
            <button className="btn ghost danger-text" type="button" onClick={remove} disabled={busy}>
              Sil
            </button>
          )}
        </div>
      </form>
    </>
  );
}
