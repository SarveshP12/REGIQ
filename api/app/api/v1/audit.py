from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import require_permissions
from app.models.audit_log import AuditLog

router = APIRouter()

@router.get("/logs", dependencies=[Depends(require_permissions("audit:read"))])
async def query_audit_logs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuditLog).limit(100))
    logs = result.scalars().all()
    return logs
