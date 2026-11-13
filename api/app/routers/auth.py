import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import Organization, User
from ..schemas import LoginIn, OrgOut, RegisterIn, TokenOut, UserOut
from ..security import create_token, hash_password, login_throttle, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

# Zamanlama farkıyla kullanıcı var/yok sızdırmamak için, olmayan kullanıcıda da aynı maliyette doğrulama yapılır
_DUMMY_HASH = hash_password("dummy-password-for-timing")


def _user_out(user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role,
                   org_id=user.org_id, org_name=user.org.name)


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(func.lower(User.email) == body.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu e-posta ile zaten bir hesap var")

    if body.role == "accountant":
        if not body.org_name or not body.org_name.strip():
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Büro adı gerekli")
        org = Organization(name=body.org_name.strip(), invite_code=secrets.token_hex(4).upper())
        db.add(org)
        db.flush()
    else:
        code = (body.invite_code or "").strip().upper()
        org = db.scalar(select(Organization).where(Organization.invite_code == code)) if code else None
        if org is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Davet kodu geçersiz")

    user = User(org_id=org.id, email=body.email, password_hash=hash_password(body.password),
                full_name=body.full_name.strip(), role=body.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_token(user.id, user.role, user.org_id), user=_user_out(user))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    key = f"{body.email}|{request.client.host if request.client else '-'}"
    if login_throttle.blocked(key):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Çok fazla başarısız deneme. Biraz sonra tekrar dene.")

    user = db.scalar(select(User).where(func.lower(User.email) == body.email))
    ok = verify_password(body.password, user.password_hash if user else _DUMMY_HASH)
    if not user or not ok or not user.is_active:
        login_throttle.record_failure(key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-posta veya şifre hatalı")

    login_throttle.reset(key)
    return TokenOut(access_token=create_token(user.id, user.role, user.org_id), user=_user_out(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return _user_out(user)


@router.get("/org", response_model=OrgOut)
def my_org(user: User = Depends(get_current_user)):
    org = user.org
    return OrgOut(id=org.id, name=org.name, invite_code=org.invite_code if user.role == "accountant" else None)
