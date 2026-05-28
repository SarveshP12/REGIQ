"""Authentication endpoints — /api/v1/auth."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)

router = APIRouter()


@router.post("/login", description="Authenticate user and return JWT tokens")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user credentials and issue JWT access + refresh tokens."""
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)

    # Generate tokens
    token_data = {"sub": str(user.id), "role": user.role, "tenant_id": str(user.tenant_id)}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    await log_audit(db, user.id, "login", "auth", tenant_id=user.tenant_id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "tenant_id": user.tenant_id,
        },
    }


@router.post("/refresh", description="Refresh access token using a valid refresh token")
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Issue a new access token using a valid refresh token."""
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    from uuid import UUID

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    token_data = {"sub": str(user.id), "role": user.role, "tenant_id": str(user.tenant_id)}
    new_access = create_access_token(data=token_data)
    new_refresh = create_refresh_token(data=token_data)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/logout", description="Invalidate the current session")
async def logout():
    """Logout — client should discard tokens. In a production setup, the refresh
    token would be added to a Redis blacklist."""
    return {"message": "Logged out successfully. Please discard your tokens."}


@router.post("/register", response_model=UserResponse, status_code=201, description="Register a new user")
async def register(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account."""
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Verify tenant exists
    tenant = await db.execute(select(Tenant).where(Tenant.id == body.tenant_id))
    if not tenant.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tenant not found")

    user = User(
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
        role=body.role,
        tenant_id=body.tenant_id,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    await log_audit(db, user.id, "register", "user", resource_id=user.id, tenant_id=user.tenant_id)

    return UserResponse.model_validate(user)
