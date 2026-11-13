"""Ayarlar: ortam değişkenlerinden (ve varsa kök dizindeki .env dosyasından) okunur."""
import os
import secrets
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

ROOT_DIR = Path(__file__).resolve().parents[2]


def _load_dotenv(path: Path) -> None:
    """Çok basit .env okuyucu. Ortamda zaten tanımlı olan değerlerin üzerine yazmaz."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(ROOT_DIR / ".env")


def _jwt_secret() -> str:
    value = os.environ.get("JWT_SECRET", "").strip()
    if not value or value.startswith("BURAYA_"):
        warnings.warn(
            "JWT_SECRET tanımlı değil: geçici rastgele bir anahtar kullanılıyor, "
            "sunucu yeniden başlayınca tüm oturumlar kapanır.",
            stacklevel=2,
        )
        return secrets.token_urlsafe(48)
    return value


@dataclass
class Settings:
    jwt_secret: str = field(default_factory=_jwt_secret)
    jwt_expire_minutes: int = int(os.environ.get("JWT_EXPIRE_MINUTES", "720"))
    database_url: str = os.environ.get("DATABASE_URL", "sqlite:///./data/app.db")
    storage_dir: Path = Path(os.environ.get("STORAGE_DIR", "./storage"))
    retention_days: int = int(os.environ.get("RETENTION_DAYS", "30"))
    max_upload_mb: int = int(os.environ.get("MAX_UPLOAD_MB", "15"))
    cors_origins: List[str] = field(
        default_factory=lambda: [
            o.strip()
            for o in os.environ.get(
                "CORS_ORIGINS", "http://localhost:5173,http://localhost:8080"
            ).split(",")
            if o.strip()
        ]
    )
    # local: veri dışarı çıkmaz | hybrid: yerel çıkarım yetmezse Claude'a sorulur
    extraction_mode: str = os.environ.get("EXTRACTION_MODE", "local")
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    extraction_llm_model: str = os.environ.get("EXTRACTION_LLM_MODEL", "claude-opus-5-5")


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
