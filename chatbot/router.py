"""FastAPI yönlendiricisi. API tarafında `build_router(get_current_user)` ile bağlanır (api/app/main.py)."""
import time
from collections import defaultdict, deque
from typing import Any, Callable, Deque, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .engine import Engine
from .llm import make_llm

RATE_LIMIT = 30          # kullanıcı başına dakikada en fazla mesaj
RATE_WINDOW = 60.0


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    client: Literal["web", "desktop", "mobile"] = "web"
    screen: Optional[str] = Field(default=None, max_length=32)   # kullanıcının o an bulunduğu ekran


class Action(BaseModel):
    type: Literal["navigate"]
    screen: str
    label: str


class ChatOut(BaseModel):
    answer: str
    steps: List[str] = []
    action: Optional[Action] = None
    suggestions: List[str] = []
    matched: Optional[str] = None
    confidence: float = 0.0
    source: str
    where: Optional[str] = None


def build_router(get_user: Callable[..., Any], engine: Optional[Engine] = None) -> APIRouter:
    """`get_user`: oturumdaki kullanıcıyı döndüren FastAPI bağımlılığı (`.id` ve `.role` alanları olmalı)."""
    eng = engine or Engine(llm=make_llm())
    router = APIRouter(prefix="/chat", tags=["chatbot"])
    hits: Dict[int, Deque[float]] = defaultdict(deque)

    def throttle(user_id: int) -> None:
        now = time.time()
        q = hits[user_id]
        while q and now - q[0] > RATE_WINDOW:
            q.popleft()
        if len(q) >= RATE_LIMIT:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Çok hızlı soruyorsun, biraz bekle.")
        q.append(now)

    @router.post("", response_model=ChatOut)
    def chat(body: ChatIn, user: Any = Depends(get_user)):
        throttle(user.id)
        return eng.answer(body.message, role=user.role, client=body.client, screen=body.screen)

    @router.get("/topics", response_model=List[str])
    def topics(client: Literal["web", "desktop", "mobile"] = "web", user: Any = Depends(get_user)):
        return eng.topics(user.role, client)

    return router
