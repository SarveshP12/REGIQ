"""JWT authentication, password hashing, and RBAC dependency helpers."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated, List, Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db

settings = get_settings()

# ── Password hashing (bcrypt directly — avoids passlib/bcrypt 4.1+ incompatibility) ──


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── JWT tokens ─────────────────────────────────────────────


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ── API Key helpers ────────────────────────────────────────


def generate_api_key() -> tuple[str, str]:
    """Return (raw_key, key_hash) pair."""
    raw = f"regiq_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    return raw, key_hash


def verify_api_key_signature(
    payload: bytes,
    signature: str,
    key: str,
) -> bool:
    """Verify HMAC-SHA256 request signature."""
    expected = hmac.new(key.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


# ── Roles & Permissions ───────────────────────────────────


class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    TEST_MANAGER = "test_manager"
    QA_ENGINEER = "qa_engineer"
    VIEWER = "viewer"
    API_SERVICE = "api_service"


# Permission matrix — each role gets a set of allowed actions
ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.SUPER_ADMIN: {
        "users:read", "users:write", "users:delete",
        "tenants:read", "tenants:write", "tenants:delete",
        "tests:read", "tests:write", "tests:delete", "tests:import", "tests:export",
        "suites:read", "suites:write", "suites:execute",
        "integrations:read", "integrations:write",
        "releases:read", "releases:write",
        "changes:read", "changes:write",
        "dashboards:read",
        "audit:read",
        "api_keys:read", "api_keys:write",
    },
    Role.TENANT_ADMIN: {
        "users:read", "users:write",
        "tests:read", "tests:write", "tests:delete", "tests:import", "tests:export",
        "suites:read", "suites:write", "suites:execute",
        "integrations:read", "integrations:write",
        "releases:read", "releases:write",
        "changes:read", "changes:write",
        "dashboards:read",
        "audit:read",
        "api_keys:read", "api_keys:write",
    },
    Role.TEST_MANAGER: {
        "tests:read", "tests:write", "tests:delete", "tests:import", "tests:export",
        "suites:read", "suites:write", "suites:execute",
        "releases:read", "releases:write",
        "changes:read",
        "dashboards:read",
        "audit:read",
    },
    Role.QA_ENGINEER: {
        "tests:read", "tests:write", "tests:import", "tests:export",
        "suites:read", "suites:execute",
        "releases:read",
        "changes:read",
        "dashboards:read",
    },
    Role.VIEWER: {
        "tests:read",
        "suites:read",
        "releases:read",
        "changes:read",
        "dashboards:read",
    },
    Role.API_SERVICE: {
        "tests:read", "tests:write", "tests:import",
        "suites:read", "suites:execute",
        "changes:read", "changes:write",
        "releases:read",
    },
}


# ── FastAPI Dependencies ───────────────────────────────────

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Decode JWT and return the User ORM object."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    # Set the PostgreSQL session variable for Row-Level Security isolation
    if tenant_id:
        from sqlalchemy import text
        await db.execute(
            text("SET LOCAL app.current_tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        )

    from app.models.user import User

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


def require_permissions(*permissions: str):
    """Return a FastAPI dependency that checks the current user has ALL listed permissions."""

    async def _checker(current_user=Depends(get_current_user)):
        user_role = Role(current_user.role)
        user_perms = ROLE_PERMISSIONS.get(user_role, set())
        missing = set(permissions) - user_perms
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(sorted(missing))}",
            )
        return current_user

    return _checker
