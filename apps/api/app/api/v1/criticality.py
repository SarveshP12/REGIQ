from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.ai.criticality import calculate_criticality
from app.core.audit import log_audit
from app.core.database import get_db
from app.core.security import get_current_user, require_permissions
from app.models.test_case import TestCase
from app.models.user import User

router = APIRouter()

class CriticalityOverrideRequest(BaseModel):
    score: float = Field(..., ge=0.0, le=10.0)
    category: str = Field(..., description="Critical, High, Medium, or Low")
    reason: str = Field(..., min_length=5)
    
class CriticalityResponse(BaseModel):
    test_case_id: UUID
    score: float
    category: str
    breakdown: Optional[Dict[str, float]] = None

@router.post(
    "/{test_case_id}/override",
    response_model=CriticalityResponse,
    dependencies=[Depends(require_permissions("tests:write"))],
)
async def override_criticality(
    test_case_id: UUID,
    body: CriticalityOverrideRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(TestCase).where(TestCase.id == test_case_id, TestCase.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    tc = result.scalar_one_or_none()
    
    if not tc:
        raise HTTPException(status_code=404, detail="Test case not found")
        
    old_score = tc.criticality_score
    old_category = tc.ai_criticality_level or tc.criticality
        
    tc.criticality_score = body.score
    tc.criticality = body.category
    tc.ai_criticality_level = body.category
    tc.updated_at = datetime.now(timezone.utc)
    
    await db.flush()
    
    await log_audit(
        db, current_user.id, "criticality_override", "test_case",
        resource_id=tc.id, tenant_id=current_user.tenant_id,
        details={
            "old_score": old_score,
            "new_score": body.score,
            "old_category": old_category,
            "new_category": body.category,
            "reason": body.reason,
        },
    )
    
    return CriticalityResponse(
        test_case_id=tc.id,
        score=body.score,
        category=body.category
    )

@router.post(
    "/{test_case_id}/recalculate",
    response_model=CriticalityResponse,
    dependencies=[Depends(require_permissions("tests:write"))],
)
async def recalculate_criticality(
    test_case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(TestCase).where(TestCase.id == test_case_id, TestCase.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt)
    tc = result.scalar_one_or_none()
    
    if not tc:
        raise HTTPException(status_code=404, detail="Test case not found")
        
    def _steps_to_text(steps):
        if not steps: return ""
        if isinstance(steps, list):
            return " ".join(str(s) for s in steps)
        return str(steps)
        
    crit_result = calculate_criticality(tc.title or "", tc.description or "", _steps_to_text(tc.steps))
    
    tc.criticality_score = crit_result["score"]
    tc.ai_criticality_level = crit_result["category"]
    tc.criticality = crit_result["category"]
    
    await db.flush()
    
    return CriticalityResponse(
        test_case_id=tc.id,
        score=crit_result["score"],
        category=crit_result["category"],
        breakdown=crit_result["breakdown"]
    )
