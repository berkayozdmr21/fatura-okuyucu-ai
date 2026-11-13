import { useAuth } from "../auth";

export default function Profile() {
  const { user, logout } = useAuth();
  if (!user) return null;
  return (
    <>
      <h1>Hesabım</h1>
      <section className="card">
        <dl className="kv">
          <dt>Ad soyad</dt>
          <dd>{user.full_name}</dd>
          <dt>E-posta</dt>
          <dd>{user.email}</dd>
          <dt>Hesap türü</dt>
          <dd>{user.role === "accountant" ? "Muhasebeci" : "Müşteri"}</dd>
          <dt>Büro</dt>
          <dd>{user.org_name}</dd>
        </dl>
        <p className="muted">
          Yüklediğin dosyalar varsayılan olarak 30 gün sonra otomatik silinir; okunan fatura verileri kayıtlı kalır.
          Şifre değiştirme özelliği henüz yok.
        </p>
        <button className="btn secondary" onClick={logout}>
          Çıkış yap
        </button>
      </section>
    </>
  );
}
