import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import ROOT_DIR, settings
from .db import init_db
from .deps import get_current_user
from .routers import auth, documents, exports


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Fatura Okuyucu API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,           # Bearer token kullanıyoruz, çerez yok
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(exports.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


# Opsiyonel modül: uygulama içi yardım asistanı (chatbot/ klasörü varsa bağlanır).
try:
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from chatbot.router import build_router  # type: ignore

    app.include_router(build_router(get_current_user))
except ModuleNotFoundError as exc:
    # Yalnızca chatbot modülü hiç yoksa sessizce atla; içindeki gerçek bir import hatasını gizleme.
    if not (exc.name or "").startswith("chatbot"):
        raise
