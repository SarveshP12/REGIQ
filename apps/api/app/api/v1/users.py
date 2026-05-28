from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user, require_permissions, generate_api_key, hash_password
from app.models.user import User

router = APIRouter()

@router.get("/", dependencies=[Depends(require_permissions("users:read"))])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [{"id": u.id, "email": u.email, "name": u.name, "role": u.role, "tenant_id": u.tenant_id} for u in users]

@router.get("/{id}", dependencies=[Depends(require_permissions("users:read"))])
async def get_user_details(id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role}

@router.put("/{id}/role", dependencies=[Depends(require_permissions("users:write"))])
async def update_user_role(id: UUID, role: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    await db.commit()
    return {"message": "Role updated"}

@router.get("/{id}/permissions", dependencies=[Depends(get_current_user)])
async def get_user_permissions(id: UUID, current_user: User = Depends(get_current_user)):
    from app.core.security import ROLE_PERMISSIONS, Role
    if current_user.id != id and current_user.role not in [Role.SUPER_ADMIN, Role.TENANT_ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    perms = ROLE_PERMISSIONS.get(Role(current_user.role), set())
    return {"permissions": list(perms)}
