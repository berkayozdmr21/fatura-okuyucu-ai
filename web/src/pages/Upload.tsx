import { useRef, useState, type DragEvent } from "react";
import { Link } from "react-router-dom";

import { api, ApiError } from "../api";
import { StatusBadge } from "../components/Badges";
import { formatAmount, formatSize } from "../format";
import type { Doc } from "../types";

interface Item {
  file: File;
  state: "waiting" | "uploading" | "done" | "error";
  doc?: Doc;
  error?: string;
  existingId?: number;
}

const ACCEPT = ".pdf,.xml,.png,.jpg,.jpeg,.webp,application/pdf,text/xml,application/xml,image/png,image/jpeg,image/webp";

export default function Upload() {
  const [items, setItems] = useState<Item[]>([]);
  const [dragging, setDragging] = useState(false);
  const busy = useRef(false);

  function patch(index: number, change: Partial<Item>) {
    setItems((all) => all.map((it, i) => (i === index ? { ...it, ...change } : it)));
  }

  async function addFiles(files: FileList | File[]) {
    const list = Array.from(files);
    if (list.length === 0 || busy.current) return;
    busy.current = true;
    const start = items.length;
    setItems((all) => [...all, ...list.map((file) => ({ file, state: "waiting" as const }))]);
    // Sırayla yükle: sunucuyu ve OCR'ı boğmamak için
    for (let i = 0; i < list.length; i++) {
      const idx = start + i;
      patch(idx, { state: "uploading" });
      try {
        const doc = await api.upload(list[i]);
        patch(idx, { state: "done", doc });
      } catch (e) {
        if (e instanceof ApiError && e.status === 409) {
          const id = (e.payload as { document_id?: number } | undefined)?.document_id;
          patch(idx, { state: "error", error: "Bu dosya zaten yüklenmiş.", existingId: id });
        } else {
          patch(idx, { state: "error", error: e instanceof Error ? e.message : "Yüklenemedi." });
        }
      }
    }
    busy.current = false;
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    void addFiles(e.dataTransfer.files);
  }

  return (
    <>
      <h1>Belge yükle</h1>
      <div
        className={`dropzone ${dragging ? "drag" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <p>
          <strong>Dosyaları buraya sürükle</strong> veya seç
        </p>
        <p className="muted">PDF, XML (e-Fatura), PNG, JPG, WEBP · en fazla 15 MB</p>
        <div className="row center">
          <label className="btn">
            Dosya seç
            <input type="file" accept={ACCEPT} multiple hidden onChange={(e) => e.target.files && void addFiles(e.target.files)} />
          </label>
          {/* Telefonda doğrudan kamerayı açar; bilgisayarda normal dosya seçici gibi davranır */}
          <label className="btn secondary">
            Fotoğraf çek
            <input
              type="file"
              accept="image/*"
              capture="environment"
              hidden
              onChange={(e) => e.target.files && void addFiles(e.target.files)}
            />
          </label>
        </div>
      </div>

      <ul className="doc-list">
        {items.map((it, i) => (
          <li key={i} className="card upload-row">
            <div>
              <strong>{it.file.name}</strong>
              <small>{formatSize(it.file.size)}</small>
            </div>
            <div className="doc-meta">
              {it.state === "waiting" && <span className="muted">Sırada</span>}
              {it.state === "uploading" && <span className="muted">Okunuyor…</span>}
              {it.state === "done" && it.doc && (
                <>
                  <span>{formatAmount(it.doc.data.total, it.doc.data.currency)}</span>
                  <StatusBadge status={it.doc.status} />
                  <Link to={`/documents/${it.doc.id}`}>Aç</Link>
                </>
              )}
              {it.state === "error" && (
                <>
                  <span className="error">{it.error}</span>
                  {it.existingId && <Link to={`/documents/${it.existingId}`}>Mevcut belgeyi aç</Link>}
                </>
              )}
            </div>
          </li>
        ))}
      </ul>
    </>
  );
}
