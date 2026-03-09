"""
JWT authentication utilities.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_session
from backend.db.models import UserRecord
from backend.utils.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer = HTTPBearer(auto_error=False)


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_access_token(subject: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


# ── FastAPI dependencies ──────────────────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> UserRecord:
    """Require a valid JWT. Raises 401 if missing/invalid."""
    if not settings.AUTH_ENABLED:
        # Auth disabled — return a synthetic admin user
        return UserRecord(id="system", email="system@local", name="System", role="admin", is_active=True)

    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await session.execute(select(UserRecord).where(UserRecord.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> Optional[UserRecord]:
    """Return user if auth token provided; None otherwise (used when AUTH_ENABLED=False)."""
    if not settings.AUTH_ENABLED:
        return None
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
        result = await session.execute(select(UserRecord).where(UserRecord.id == user_id))
        return result.scalar_one_or_none()
    except JWTError:
        return None


def require_role(*roles: str):
    """Dependency factory: requires user to have one of the specified roles."""
    async def _check(user: UserRecord = Depends(get_current_user)) -> UserRecord:
        if settings.AUTH_ENABLED and user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return _check
