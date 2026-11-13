"""Muhasebeci için Excel/CSV dışa aktarım.

Belgelerden gelen metinler güvenilmezdir: '=', '+', '-', '@' ile başlayan hücreler Excel'de formül
olarak çalışabileceğinden (CSV/formül enjeksiyonu) başlarına tek tırnak eklenir.
"""
import csv
import io
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query, Response
from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_accountant
from ..models import AuditLog, Document, User

router = APIRouter(prefix="/exports", tags=["exports"])

COLUMNS = [
    ("Tarih", "invoice_date"), ("Belge No", "invoice_no"), ("Cari Unvan", "seller_name"), ("VKN/TCKN", "seller_vkn"),
    ("Matrah", "subtotal"), ("KDV Oranı (%)", "vat_rate"), ("KDV Tutarı", "vat_amount"), ("Genel Toplam", "total"),
    ("Para Birimi", "currency"),
]
_DANGEROUS = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(value: Any) -> Any:
    if isinstance(value, str) and value.startswith(_DANGEROUS):
        return "'" + value
    return value


def _rows(db: Session, user: User, status: Optional[str]) -> List[Document]:
    q = select(Document).where(Document.org_id == user.org_id)
    if status:
        q = q.where(Document.status == status)
    return list(db.scalars(q.order_by(Document.created_at, Document.id)))


def _record(doc: Document) -> list:
    return [safe_cell((doc.data or {}).get(key)) for _, key in COLUMNS]


@router.get("/documents.xlsx")
def export_xlsx(status: Optional[str] = Query(default="approved"), db: Session = Depends(get_db),
                user: User = Depends(require_accountant)):
    docs = _rows(db, user, status)
    wb = Workbook()
    ws = wb.active
    ws.title = "Faturalar"
    ws.append([name for name, _ in COLUMNS])
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for doc in docs:
        ws.append(_record(doc))
    for idx, width in enumerate([12, 22, 36, 14, 14, 14, 14, 14, 12], start=1):
        ws.column_dimensions[chr(64 + idx)].width = width
    buf = io.BytesIO()
    wb.save(buf)
    db.add(AuditLog(org_id=user.org_id, user_id=user.id, action="export", detail={"format": "xlsx", "count": len(docs)}))
    db.commit()
    return Response(buf.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="faturalar.xlsx"'})


@router.get("/documents.csv")
def export_csv(status: Optional[str] = Query(default="approved"), db: Session = Depends(get_db),
               user: User = Depends(require_accountant)):
    docs = _rows(db, user, status)
    out = io.StringIO()
    # Türkçe Excel ayırıcısı ';' ve ondalık ayracı ',' kullanır
    writer = csv.writer(out, delimiter=";")
    writer.writerow([name for name, _ in COLUMNS])
    for doc in docs:
        writer.writerow(["" if v is None else (str(v).replace(".", ",") if isinstance(v, float) else v)
                         for v in _record(doc)])
    db.add(AuditLog(org_id=user.org_id, user_id=user.id, action="export", detail={"format": "csv", "count": len(docs)}))
    db.commit()
    # utf-8-sig: Excel'in Türkçe karakterleri doğru açması için BOM
    return Response(("﻿" + out.getvalue()).encode("utf-8"), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="faturalar.csv"'})
