import hashlib
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..deps import get_current_user, require_accountant
from ..extraction import extract_document
from ..extraction.parsing import only_digits, parse_amount, parse_date
from ..extraction.schema import FIELDS
from ..extraction.validators import decide_review, effective_confidence, validate
from ..models import AuditLog, Document, User, utcnow
from ..schemas import DocumentOut, DocumentPatch

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTS = {".pdf", ".xml", ".png", ".jpg", ".jpeg", ".webp"}
MIME_BY_EXT = {".pdf": "application/pdf", ".xml": "application/xml", ".png": "image/png",
               ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def _magic_ok(ext: str, head: bytes) -> bool:
    """Uzantı ile gerçek dosya içeriğinin uyuştuğunu doğrular (yanlış etiketli dosyaları reddeder)."""
    if ext == ".pdf":
        return head.startswith(b"%PDF")
    if ext == ".png":
        return head.startswith(b"\x89PNG")
    if ext in (".jpg", ".jpeg"):
        return head.startswith(b"\xff\xd8")
    if ext == ".webp":
        return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    if ext == ".xml":
        return head.lstrip(b"\xef\xbb\xbf \t\r\n").startswith(b"<")
    return False


def _audit(db: Session, user: User, action: str, doc: Optional[Document] = None, detail: Optional[dict] = None):
    db.add(AuditLog(org_id=user.org_id, user_id=user.id, document_id=doc.id if doc else None,
                    action=action, detail=detail or {}))


def _out(doc: Document) -> DocumentOut:
    return DocumentOut(
        id=doc.id, original_filename=doc.original_filename, mime_type=doc.mime_type, size_bytes=doc.size_bytes,
        status=doc.status, extractor=doc.extractor, data=doc.data or {},
        field_confidence=effective_confidence(doc.field_confidence or {}, doc.issues or []),
        issues=doc.issues or [], needs_review=doc.needs_review, has_file=bool(doc.storage_path),
        uploader_id=doc.uploader_id, created_at=doc.created_at, expires_at=doc.expires_at,
    )


def scoped(db: Session, user: User):
    """Kullanıcının görebileceği belgeler: muhasebeci -> büronun tümü, müşteri -> yalnızca kendi yüklediği."""
    q = select(Document).where(Document.org_id == user.org_id)
    if user.role == "client":
        q = q.where(Document.uploader_id == user.id)
    return q


def get_doc_or_404(db: Session, user: User, doc_id: int) -> Document:
    doc = db.scalar(scoped(db, user).where(Document.id == doc_id))
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Belge bulunamadı")
    return doc


def _find_duplicate_invoice(db: Session, org_id: int, doc_id: int, data: Dict[str, Any]) -> Optional[Document]:
    vkn, no = data.get("seller_vkn"), data.get("invoice_no")
    if not vkn or not no:
        return None
    return db.scalar(
        select(Document).where(
            Document.org_id == org_id,
            Document.id != doc_id,
            Document.data["seller_vkn"].as_string() == str(vkn),
            Document.data["invoice_no"].as_string() == str(no),
            Document.status != "rejected",
        )
    )


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    name = Path(file.filename or "belge").name
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Desteklenen türler: PDF, XML, PNG, JPG, WEBP")

    limit = settings.max_upload_mb * 1024 * 1024
    chunks, size = [], 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        size += len(chunk)
        if size > limit:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                f"Dosya {settings.max_upload_mb} MB sınırını aşıyor")
        chunks.append(chunk)
    content = b"".join(chunks)
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dosya boş")
    if not _magic_ok(ext, content[:16]):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dosya içeriği uzantısıyla uyuşmuyor")

    sha = hashlib.sha256(content).hexdigest()
    existing = db.scalar(select(Document).where(Document.org_id == user.org_id, Document.sha256 == sha))
    if existing is not None:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT,
                            content={"detail": "Bu dosya zaten yüklenmiş", "document_id": existing.id})

    mime = MIME_BY_EXT[ext]
    result = extract_document(content, name, mime)

    storage_dir = Path(settings.storage_dir) / f"org_{user.org_id}"
    storage_dir.mkdir(parents=True, exist_ok=True)
    path = storage_dir / f"{sha}{ext}"
    path.write_bytes(content)

    doc = Document(
        org_id=user.org_id, uploader_id=user.id, original_filename=name, mime_type=mime, size_bytes=size, sha256=sha,
        storage_path=str(path), extractor=result.extractor, data=result.data, field_confidence=result.confidence,
        issues=result.issues, needs_review=result.needs_review,
        status="failed" if result.failed else ("needs_review" if result.needs_review else "processed"),
        expires_at=utcnow() + timedelta(days=settings.retention_days) if settings.retention_days > 0 else None,
    )
    db.add(doc)
    db.flush()

    dup = _find_duplicate_invoice(db, doc.org_id, doc.id, doc.data)
    if dup is not None:
        doc.issues = list(doc.issues) + [{
            "code": "duplicate_invoice", "field": "invoice_no", "severity": "error",
            "message": f"Aynı satıcı ve fatura numarası #{dup.id} numaralı belgede de var."}]
        doc.needs_review = True
        if doc.status == "processed":
            doc.status = "needs_review"

    _audit(db, user, "upload", doc, {"filename": name, "extractor": result.extractor})
    db.commit()
    db.refresh(doc)
    return _out(doc)


@router.get("", response_model=List[DocumentOut])
def list_documents(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    q: Optional[str] = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = scoped(db, user)
    if status_filter:
        query = query.where(Document.status == status_filter)
    if q:
        query = query.where(Document.original_filename.ilike(f"%{q}%"))
    docs = db.scalars(query.order_by(Document.created_at.desc(), Document.id.desc()).limit(limit).offset(offset))
    return [_out(d) for d in docs]


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _out(get_doc_or_404(db, user, doc_id))


@router.get("/{doc_id}/file")
def download_file(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = get_doc_or_404(db, user, doc_id)
    if not doc.storage_path or not Path(doc.storage_path).is_file():
        raise HTTPException(status.HTTP_410_GONE, "Dosya saklama süresi dolduğu için silindi")
    _audit(db, user, "view", doc)
    db.commit()
    return FileResponse(doc.storage_path, media_type=doc.mime_type, filename=doc.original_filename)


def _coerce(field: str, value: Any):
    if value in (None, ""):
        return None
    if field in ("seller_vkn", "buyer_vkn"):
        return only_digits(str(value)) or None
    if field == "invoice_date":
        return parse_date(str(value)) or None
    if field in ("subtotal", "vat_amount", "total"):
        return float(value) if isinstance(value, (int, float)) else parse_amount(str(value))
    if field == "vat_rate":
        v = float(value) if isinstance(value, (int, float)) else parse_amount(str(value))
        return int(v) if v is not None and float(v).is_integer() else v
    if field == "invoice_no":
        return str(value).strip().upper()
    if field == "currency":
        return str(value).strip().upper()[:3]
    return str(value).strip()


@router.patch("/{doc_id}", response_model=DocumentOut)
def review_document(doc_id: int, body: DocumentPatch, db: Session = Depends(get_db),
                    user: User = Depends(require_accountant)):
    doc = get_doc_or_404(db, user, doc_id)

    if body.data is not None:
        unknown = set(body.data) - set(FIELDS)
        if unknown:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Bilinmeyen alan(lar): {sorted(unknown)}")
        data: Dict[str, Any] = dict(doc.data or {})
        conf: Dict[str, float] = dict(doc.field_confidence or {})
        for field, raw in body.data.items():
            data[field] = _coerce(field, raw)
            conf[field] = 1.0          # insan düzeltmesi
        issues = validate(data)
        dup = _find_duplicate_invoice(db, doc.org_id, doc.id, data)
        if dup is not None:
            issues.append({"code": "duplicate_invoice", "field": "invoice_no", "severity": "error",
                           "message": f"Aynı satıcı ve fatura numarası #{dup.id} numaralı belgede de var."})
        doc.data, doc.field_confidence, doc.issues = data, conf, issues
        doc.needs_review = decide_review(issues, conf)
        if doc.status in ("processed", "needs_review", "failed"):
            doc.status = "needs_review" if doc.needs_review else "processed"
        _audit(db, user, "edit", doc, {"fields": sorted(body.data)})

    if body.status is not None:
        doc.status = body.status
        doc.needs_review = body.status == "needs_review"
        if body.status in ("approved", "rejected"):
            doc.reviewed_by, doc.reviewed_at = user.id, utcnow()
        _audit(db, user, "approve" if body.status == "approved" else body.status, doc)

    db.commit()
    db.refresh(doc)
    return _out(doc)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = get_doc_or_404(db, user, doc_id)
    if user.role == "client" and doc.status == "approved":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Onaylanmış belgeyi yalnızca muhasebeci silebilir")
    if doc.storage_path:
        Path(doc.storage_path).unlink(missing_ok=True)
    _audit(db, user, "delete", None, {"document_id": doc.id, "filename": doc.original_filename})
    db.delete(doc)
    db.commit()
