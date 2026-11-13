import os
import shutil
import tempfile
from pathlib import Path

# Ayarlar uygulama içe aktarılmadan ÖNCE verilmeli
_tmp = Path(tempfile.mkdtemp(prefix="fatura_test_"))
os.environ["JWT_SECRET"] = "test-secret-only-for-tests-0123456789"
os.environ["DATABASE_URL"] = f"sqlite:///{(_tmp / 'test.db').as_posix()}"
os.environ["STORAGE_DIR"] = str(_tmp / "storage")
os.environ["RETENTION_DAYS"] = "30"
os.environ["EXTRACTION_MODE"] = "local"
os.environ["ANTHROPIC_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.security import login_throttle  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    from app import models  # noqa: F401

    Base.metadata.create_all(engine)
    login_throttle._fails.clear()
    shutil.rmtree(os.environ["STORAGE_DIR"], ignore_errors=True)
    with TestClient(app) as c:
        yield c


def register(client, email, role, **extra):
    body = {"email": email, "password": "Sifre12345", "full_name": "Test Kullanıcı", "role": role, **extra}
    r = client.post("/auth/register", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def office(client):
    """Bir muhasebe bürosu + muhasebeci + müşteri hazırlar."""
    acc = register(client, "muhasebeci@example.com", "accountant", org_name="Test Muhasebe")
    code = client.get("/auth/org", headers=auth(acc["access_token"])).json()["invite_code"]
    cli = register(client, "musteri@example.com", "client", invite_code=code)
    return {"acc": auth(acc["access_token"]), "cli": auth(cli["access_token"]), "code": code}
