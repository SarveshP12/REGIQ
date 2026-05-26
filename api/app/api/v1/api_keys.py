from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user, require_permissions, generate_api_key
from app.models.api_key import APIKey
from app.models.user import User
from datetime import datetime, timedelta, timezone

router = APIRouter()

@router.post("/", dependencies=[Depends(require_permissions("api_keys:write"))])
async def create_api_key(
    name: str,
    expires_in_days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    raw_key, key_hash = generate_api_key()
    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    db_key = APIKey(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        key_hash=key_hash,
        expires_at=expires_at,
        scopes=["*"]
    )
    db.add(db_key)
    await db.commit()
    await db.refresh(db_key)

    return {
        "id": db_key.id,
        "name": name,
        "raw_key": raw_key,
        "expires_at": expires_at,
        "message": "Store this raw_key safely, it will not be shown again."
    }
