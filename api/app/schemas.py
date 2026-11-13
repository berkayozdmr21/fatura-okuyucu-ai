import re
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterIn(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    role: Literal["accountant", "client"]
    org_name: Optional[str] = Field(default=None, max_length=160)      # muhasebeci için zorunlu
    invite_code: Optional[str] = Field(default=None, max_length=32)    # müşteri için zorunlu

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("Geçerli bir e-posta adresi girin")
        return v


class LoginIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return v.strip().lower()


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    org_id: int
    org_name: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class OrgOut(BaseModel):
    id: int
    name: str
    invite_code: Optional[str] = None   # yalnızca muhasebeciye gösterilir


class DocumentOut(BaseModel):
    id: int
    original_filename: str
    mime_type: str
    size_bytes: int
    status: str
    extractor: Optional[str]
    data: Dict[str, Any]
    field_confidence: Dict[str, float]
    issues: List[Dict[str, Any]]
    needs_review: bool
    has_file: bool
    uploader_id: int
    created_at: datetime
    expires_at: Optional[datetime]


class DocumentPatch(BaseModel):
    data: Optional[Dict[str, Any]] = None
    status: Optional[Literal["approved", "rejected", "needs_review"]] = None

