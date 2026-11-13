import { useEffect, useState } from "react";

import { api } from "../api";
import type { Org } from "../types";

export default function Team() {
  const [org, setOrg] = useState<Org | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.org().then(setOrg).catch((e: Error) => setError(e.message));
  }, []);

  async function copy() {
    if (!org?.invite_code) return;
    try {
      await navigator.clipboard.writeText(org.invite_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* pano erişimi yoksa kullanıcı kodu elle kopyalar */
    }
  }

  return (
    <>
      <h1>Büro ve davet kodu</h1>
      {error && <p className="error">{error}</p>}
      {org && (
        <section className="card">
          <p>
            Büro: <strong>{org.name}</strong>
          </p>
          <p>Müşterilerin kayıt olurken bu kodu girmesi gerekir. Müşteri yalnızca kendi yüklediği belgeleri görür.</p>
          <p className="invite">
            <code>{org.invite_code}</code>
            <button className="btn secondary small" onClick={copy}>
              {copied ? "Kopyalandı" : "Kopyala"}
            </button>
          </p>
        </section>
      )}
    </>
  );
}
