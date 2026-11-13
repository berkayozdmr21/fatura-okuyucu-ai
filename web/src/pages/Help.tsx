export default function Help() {
  return (
    <>
      <h1>Yardım</h1>
      <section className="card">
        <h2>Sık sorulanlar</h2>
        <p>
          Bir şeyi bulamazsan sağ alttaki <strong>“Yardım?”</strong> düğmesiyle asistana sorabilirsin; sana adımları anlatır ve seni
          doğrudan ilgili ekrana götürür.
        </p>
        <ul>
          <li>Belge yüklemek için “Belge Yükle” ekranını kullan; telefonda “Fotoğraf çek” ile doğrudan kamerayı açabilirsin.</li>
          <li>“İncelemede” durumundaki belgelerde bir alan şüpheli görünür; muhasebeci kontrol edip onaylar.</li>
          <li>Müşteri hesabında yalnızca kendi yüklediğin belgeler görünür.</li>
        </ul>
        <p className="muted">Çözemediğin bir sorun için bürondaki muhasebeciyle iletişime geç.</p>
      </section>
    </>
  );
}
