from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatbot import router as router_mod
from chatbot.router import build_router


def make_app(role="client", uid=1):
    app = FastAPI()
    user = SimpleNamespace(id=uid, role=role)
    app.include_router(build_router(lambda: user))
    return TestClient(app)


def test_chat_returns_action_for_the_asked_client():
    c = make_app("client")
    r = c.post("/chat", json={"message": "yükleme butonu nerede", "client": "mobile"})
    assert r.status_code == 200
    body = r.json()
    assert body["matched"] == "upload" and body["action"]["screen"] == "upload"
    assert "Alt menüdeki" in body["answer"]


def test_role_comes_from_the_session_not_from_the_request():
    """Müşteri, istek gövdesinde rol iddia ederek muhasebeci özelliklerini açamaz."""
    c = make_app("client")
    r = c.post("/chat", json={"message": "excel olarak indir", "client": "web", "role": "accountant"})
    assert r.json()["source"] == "restricted"


def test_validation_errors():
    c = make_app()
    assert c.post("/chat", json={"message": ""}).status_code == 422
    assert c.post("/chat", json={"message": "x" * 1001}).status_code == 422
    assert c.post("/chat", json={"message": "merhaba", "client": "tv"}).status_code == 422


def test_topics_endpoint():
    c = make_app("accountant")
    r = c.get("/chat/topics", params={"client": "web"})
    assert r.status_code == 200 and len(r.json()) >= 5


def test_rate_limit(monkeypatch):
    monkeypatch.setattr(router_mod, "RATE_LIMIT", 3)
    c = make_app(uid=99)
    codes = [c.post("/chat", json={"message": "merhaba"}).status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
