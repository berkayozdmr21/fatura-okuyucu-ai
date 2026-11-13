import hashlib
import io
from pathlib import Path

from app.config import settings
from app.routers.exports import safe_cell
from eval.generate import generate
from tests.conftest import auth, register

CLEAN = [c for c in generate(n=40, seed=21) if c.kind == "clean"]


def upload(client, headers, case):
    return client.post("/documents", headers=headers, files={"file": (case.name, case.content, case.mime)})


# ---------- kimlik doğrulama ----------

def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_documents_require_auth(client):
    assert client.get("/documents").status_code == 401
    assert client.get("/documents", headers=auth("sahte.token.degeri")).status_code == 401


def test_register_login_and_me(client):
    reg = register(client, "a@example.com", "accountant", org_name="Büro")
    r = client.post("/auth/login", json={"email": "A@Example.com", "password": "Sifre12345"})
    assert r.status_code == 200
    me = client.get("/auth/me", headers=auth(r.json()["access_token"])).json()
    assert me["role"] == "accountant" and me["org_name"] == "Büro"
    assert reg["user"]["email"] == "a@example.com"


def test_register_validation(client):
    base = {"email": "x@example.com", "password": "Sifre12345", "full_name": "Test Kişi"}
    assert client.post("/auth/register", json={**base, "role": "accountant"}).status_code == 422      # büro adı yok
    assert client.post("/auth/register", json={**base, "role": "client", "invite_code": "YOK"}).status_code == 400
    assert client.post("/auth/register", json={**base, "role": "client", "password": "kisa"}).status_code == 422
    assert client.post("/auth/register", json={**base, "email": "bozuk", "role": "accountant", "org_name": "B"}
                       ).status_code == 422


def test_duplicate_email_rejected(client):
    register(client, "d@example.com", "accountant", org_name="B1")
    r = client.post("/auth/register", json={"email": "D@example.com", "password": "Sifre12345",
                                            "full_name": "Başka Biri", "role": "accountant", "org_name": "B2"})
    assert r.status_code == 409


def test_wrong_password_and_throttle(client):
    register(client, "t@example.com", "accountant", org_name="B")
    for _ in range(5):
        assert client.post("/auth/login", json={"email": "t@example.com", "password": "yanlis-sifre"}).status_code == 401
    # 6. deneme doğru şifreyle bile engellenir
    assert client.post("/auth/login", json={"email": "t@example.com", "password": "Sifre12345"}).status_code == 429


def test_unknown_user_same_error_as_wrong_password(client):
    r = client.post("/auth/login", json={"email": "yok@example.com", "password": "Sifre12345"})
    assert r.status_code == 401 and "hatalı" in r.json()["detail"]


def test_invite_code_only_visible_to_accountant(client, office):
    assert client.get("/auth/org", headers=office["acc"]).json()["invite_code"] == office["code"]
    assert client.get("/auth/org", headers=office["cli"]).json()["invite_code"] is None


# ---------- belge akışı ----------

def test_upload_extracts_and_lists(client, office):
    r = upload(client, office["cli"], CLEAN[0])
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["status"] == "processed" and doc["data"]["total"] == CLEAN[0].truth["total"]
    assert doc["has_file"] is True and doc["expires_at"] is not None
    assert [d["id"] for d in client.get("/documents", headers=office["acc"]).json()] == [doc["id"]]


def test_duplicate_file_returns_409_with_id(client, office):
    first = upload(client, office["cli"], CLEAN[0]).json()
    r = upload(client, office["cli"], CLEAN[0])
    assert r.status_code == 409 and r.json()["document_id"] == first["id"]


def test_client_sees_only_own_documents_accountant_sees_all(client, office):
    other = register(client, "musteri2@example.com", "client", invite_code=office["code"])
    upload(client, office["cli"], CLEAN[0])
    upload(client, auth(other["access_token"]), CLEAN[1])
    assert len(client.get("/documents", headers=office["acc"]).json()) == 2
    mine = client.get("/documents", headers=office["cli"]).json()
    assert len(mine) == 1
    # Başkasının belgesine doğrudan erişim 404
    other_id = client.get("/documents", headers=auth(other["access_token"])).json()[0]["id"]
    assert client.get(f"/documents/{other_id}", headers=office["cli"]).status_code == 404


def test_organizations_are_isolated(client, office):
    upload(client, office["cli"], CLEAN[0])
    rival = register(client, "rakip@example.com", "accountant", org_name="Rakip Büro")
    assert client.get("/documents", headers=auth(rival["access_token"])).json() == []
    doc_id = client.get("/documents", headers=office["acc"]).json()[0]["id"]
    assert client.get(f"/documents/{doc_id}", headers=auth(rival["access_token"])).status_code == 404
    assert client.get(f"/documents/{doc_id}/file", headers=auth(rival["access_token"])).status_code == 404


def test_duplicate_invoice_number_is_flagged(client, office):
    a = CLEAN[0]
    upload(client, office["cli"], a)
    # Aynı fatura, farklı dosya baytları (başka bir PDF olarak yeniden üretilmiş gibi)
    b = type(a)(a.name.replace("case", "copy"), a.content + b"\n%dummy", a.mime, a.truth, a.kind, a.template)
    r = upload(client, office["cli"], b)
    if a.mime == "application/pdf":
        assert any(i["code"] == "duplicate_invoice" for i in r.json()["issues"])
        assert r.json()["status"] == "needs_review"


def test_rejects_wrong_extension_and_fake_content(client, office):
    r = client.post("/documents", headers=office["cli"], files={"file": ("x.exe", b"MZ....", "application/octet-stream")})
    assert r.status_code == 415
    r = client.post("/documents", headers=office["cli"], files={"file": ("fake.pdf", b"bu pdf degil", "application/pdf")})
    assert r.status_code == 400


def test_rejects_empty_and_oversized(client, office, monkeypatch):
    assert client.post("/documents", headers=office["cli"], files={"file": ("e.pdf", b"", "application/pdf")}
                       ).status_code == 400
    monkeypatch.setattr(settings, "max_upload_mb", 0)
    r = client.post("/documents", headers=office["cli"], files={"file": ("b.pdf", b"%PDF" + b"0" * 100, "application/pdf")})
    assert r.status_code == 413


def test_path_traversal_filename_is_neutralised(client, office):
    case = CLEAN[0]
    r = client.post("/documents", headers=office["cli"],
                    files={"file": ("../../evil.pdf", case.content, "application/pdf")})
    if case.mime == "application/pdf":
        assert r.status_code == 201
        assert r.json()["original_filename"] == "evil.pdf"


def test_only_accountant_can_review(client, office):
    doc = upload(client, office["cli"], CLEAN[0]).json()
    assert client.patch(f"/documents/{doc['id']}", headers=office["cli"], json={"status": "approved"}).status_code == 403
    r = client.patch(f"/documents/{doc['id']}", headers=office["acc"], json={"status": "approved"})
    assert r.status_code == 200 and r.json()["status"] == "approved"


def test_edit_revalidates_and_clears_review(client, office):
    bad = next(c for c in generate(n=80, seed=3) if c.kind == "bad_total" and c.mime == "application/pdf")
    doc = upload(client, office["cli"], bad).json()
    assert doc["needs_review"] is True
    fixed = client.patch(f"/documents/{doc['id']}", headers=office["acc"],
                         json={"data": {"total": bad.truth["total"]}}).json()
    assert fixed["needs_review"] is False and fixed["field_confidence"]["total"] == 1.0
    assert client.patch(f"/documents/{doc['id']}", headers=office["acc"],
                        json={"data": {"bilinmeyen": 1}}).status_code == 422


def test_client_cannot_delete_approved(client, office):
    doc = upload(client, office["cli"], CLEAN[0]).json()
    client.patch(f"/documents/{doc['id']}", headers=office["acc"], json={"status": "approved"})
    assert client.delete(f"/documents/{doc['id']}", headers=office["cli"]).status_code == 403
    assert client.delete(f"/documents/{doc['id']}", headers=office["acc"]).status_code == 204


def test_delete_removes_file_from_disk(client, office):
    doc = upload(client, office["cli"], CLEAN[0]).json()
    sha = hashlib.sha256(CLEAN[0].content).hexdigest()
    path = Path(settings.storage_dir) / "org_1" / f"{sha}.pdf"
    assert path.exists()
    assert client.delete(f"/documents/{doc['id']}", headers=office["cli"]).status_code == 204
    assert not path.exists()
    assert client.get(f"/documents/{doc['id']}", headers=office["cli"]).status_code == 404


def test_file_download(client, office):
    doc = upload(client, office["cli"], CLEAN[0]).json()
    r = client.get(f"/documents/{doc['id']}/file", headers=office["cli"])
    assert r.status_code == 200 and r.content == CLEAN[0].content


def test_purge_expired_files(client, office):
    from datetime import timedelta

    from sqlalchemy import select

    from app.cli import purge_expired
    from app.db import SessionLocal
    from app.models import Document, utcnow

    doc = upload(client, office["cli"], CLEAN[0]).json()
    with SessionLocal() as db:
        d = db.scalar(select(Document).where(Document.id == doc["id"]))
        d.expires_at = utcnow() - timedelta(days=1)
        db.commit()
    assert purge_expired() == 1
    r = client.get(f"/documents/{doc['id']}/file", headers=office["cli"])
    assert r.status_code == 410
    assert client.get(f"/documents/{doc['id']}", headers=office["cli"]).json()["has_file"] is False


# ---------- dışa aktarım ----------

def test_export_requires_accountant(client, office):
    assert client.get("/exports/documents.xlsx", headers=office["cli"]).status_code == 403


def test_export_xlsx_and_csv_contain_only_approved(client, office):
    ids = [upload(client, office["cli"], c).json()["id"] for c in CLEAN[:3]]
    client.patch(f"/documents/{ids[0]}", headers=office["acc"], json={"status": "approved"})
    csv_r = client.get("/exports/documents.csv", headers=office["acc"])
    assert csv_r.status_code == 200
    text = csv_r.content.decode("utf-8-sig")
    assert len(text.strip().splitlines()) == 2        # başlık + 1 onaylı belge
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(client.get("/exports/documents.xlsx", headers=office["acc"]).content))
    assert wb.active.max_row == 2


def test_safe_cell_blocks_formula_injection():
    assert safe_cell("=HYPERLINK(\"http://kotu\")") == "'=HYPERLINK(\"http://kotu\")"
    assert safe_cell("+1") == "'+1" and safe_cell("@x") == "'@x" and safe_cell("-5") == "'-5"
    assert safe_cell("Normal Ltd.") == "Normal Ltd." and safe_cell(12.5) == 12.5 and safe_cell(None) is None
