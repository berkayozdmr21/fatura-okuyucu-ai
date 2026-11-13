"""Bakım komutları.  Kullanım:  python -m app.cli purge"""
import sys
from pathlib import Path

from sqlalchemy import select

from .db import SessionLocal, init_db
from .models import Document, utcnow


def purge_expired() -> int:
    """KVKK: saklama süresi dolan belgelerin DOSYASINI siler; çıkarılan veri kaydı kalır."""
    init_db()
    removed = 0
    with SessionLocal() as db:
        docs = db.scalars(select(Document).where(
            Document.expires_at.is_not(None), Document.expires_at < utcnow(), Document.storage_path.is_not(None)))
        for doc in docs:
            Path(doc.storage_path).unlink(missing_ok=True)
            doc.storage_path = None
            removed += 1
        db.commit()
    return removed


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "purge":
        print(f"{purge_expired()} dosya silindi")
    else:
        print("Kullanım: python -m app.cli purge")
        sys.exit(2)
