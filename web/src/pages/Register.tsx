import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../api";
import { useAuth } from "../auth";

export default function Register() {
  const { register } = useAuth();
  const [role, setRole] = useState<"accountant" | "client">("client");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [orgName, setOrgName] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await register({
        email,
        password,
        full_name: fullName,
        role,
        ...(role === "accountant" ? { org_name: orgName } : { invite_code: inviteCode }),
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Kayıt yapılamadı.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <h1>Kayıt ol</h1>
        <fieldset className="role-switch">
          <legend>Hesap türü</legend>
          <label>
            <input type="radio" name="role" checked={role === "client"} onChange={() => setRole("client")} /> Müşteri
          </label>
          <label>
            <input type="radio" name="role" checked={role === "accountant"} onChange={() => setRole("accountant")} />{" "}
            Muhasebeci
          </label>
        </fieldset>
        <label>
          Ad soyad
          <input value={fullName} onChange={(e) => setFullName(e.target.value)} required minLength={2} autoComplete="name" />
        </label>
        <label>
          E-posta
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="username" />
        </label>
        <label>
          Şifre (en az 8 karakter)
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            autoComplete="new-password"
          />
        </label>
        {role === "accountant" ? (
          <label>
            Büro adı
            <input value={orgName} onChange={(e) => setOrgName(e.target.value)} required />
          </label>
        ) : (
          <label>
            Davet kodu (muhasebecinden al)
            <input value={inviteCode} onChange={(e) => setInviteCode(e.target.value)} required autoCapitalize="characters" />
          </label>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button className="btn" disabled={busy}>
          {busy ? "Kaydediliyor…" : "Kayıt ol"}
        </button>
        <p className="muted">
          Zaten hesabın var mı? <Link to="/login">Giriş yap</Link>
        </p>
      </form>
    </div>
  );
}
