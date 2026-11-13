-- KVKK: süresi dolan belgelerin dosya yolunu temizler (veri kaydı kalır, dosya silinir).
-- Önce bu sorgu dönen storage_path değerlerindeki dosyaları diskten sil (API: `python -m app.cli purge`
-- bunu otomatik yapar), ardından satırları güncelle.

SELECT id, storage_path
FROM documents
WHERE expires_at IS NOT NULL
  AND expires_at < now()
  AND storage_path IS NOT NULL;

UPDATE documents
SET storage_path = NULL, updated_at = now()
WHERE expires_at IS NOT NULL
  AND expires_at < now()
  AND storage_path IS NOT NULL;
