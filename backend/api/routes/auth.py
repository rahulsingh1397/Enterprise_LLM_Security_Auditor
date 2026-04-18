"""
Authentication routes: register, login, me, refresh.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from db.database import get_session
from db.models import AuditLog, UserRecord
from utils.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    role: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: datetime | None


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _user_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(UserRecord))
    return result.scalar_one()


async def _log(session: AsyncSession, action: str, user_id: str | None,
               resource_id: str | None = None, resource_type: str | None = None,
               detail: str | None = None, ip: str | None = None):
    session.add(AuditLog(
        user_id=user_id, action=action,
        resource_id=resource_id, resource_type=resource_type,
        detail=detail, ip_address=ip,
    ))


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, request: Request, session: AsyncSession = Depends(get_session)):
    existing = await session.execute(select(UserRecord).where(UserRecord.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    count = await _user_count(session)
    role = "admin" if count == 0 else "analyst"   # first user becomes admin

    user = UserRecord(
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
        role=role,
    )
    session.add(user)
    await session.flush()   # get user.id before commit

    await _log(session, "user_registered", user.id, user.id, "user",
               f"Registered as {role}", request.client.host if request.client else None)
    await session.commit()

    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, user_id=user.id, name=user.name, role=user.role)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(UserRecord).where(UserRecord.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    user.last_login = datetime.now(timezone.utc)
    await _log(session, "login", user.id, ip=request.client.host if request.client else None)
    await session.commit()

    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, user_id=user.id, name=user.name, role=user.role)


@router.get("/me", response_model=UserOut)
async def me(user: UserRecord = Depends(get_current_user)):
    return UserOut(
        id=user.id, email=user.email, name=user.name, role=user.role,
        is_active=user.is_active, created_at=user.created_at, last_login=user.last_login,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(user: UserRecord = Depends(get_current_user)):
    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, user_id=user.id, name=user.name, role=user.role)


@router.get("/status")
async def auth_status():
    return {"auth_enabled": settings.AUTH_ENABLED}
