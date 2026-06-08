"""AI Classification endpoints — /api/v1/ai/classify.

Provides:
  - POST /classify         — classify a single test case
  - POST /classify/batch   — classify multiple test cases
  - POST /classify/feedback — submit human correction/override
  - GET  /classify/review-queue — get low-confidence items for review
"""

import math
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai.classifier import classify_test_case, classify_batch
from app.core.audit import log_audit
from app.core.database import get_db
from app.core.security import get_current_user, require_permissions
from app.models.classification_feedback import ClassificationFeedback
from app.models.test_case import TestCase
from app.models.user import User
from app.schemas.classification import (
    ClassificationDimension,
    ClassificationFeedbackRequest,
    ClassificationFeedbackResponse,
    ClassificationResponse,
    ClassifyBatchRequest,
    ClassifyBatchResponse,
    ClassifyRequest,
    ReviewQueueItem,
    ReviewQueueResponse,
)

router = APIRouter()


# ── Single Classification ────────────────────────────────


@router.post(
    "/classify",
    response_model=ClassificationResponse,
    dependencies=[Depends(require_permissions("tests:write"))],
)
async def classify_single(
    body: ClassifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClassificationResponse:
    """Classify a single test case across 6 dimensions.

    If test_case_id is provided, the classification is persisted to the
    test case record. Otherwise, returns classification without persisting.
    """
    # Get steps as text if test_case_id is provided
    steps_text: Optional[str] = None
    if body.test_case_id:
        tc = await _get_test_or_404(db, body.test_case_id, current_user.tenant_id)
        steps_text = _steps_to_text(tc.steps) if tc.steps else None
    elif body.steps:
        steps_text = body.steps

    result = classify_test_case(
        title=body.title,
        description=body.description,
        steps=steps_text,
    )

    now = datetime.now(timezone.utc)

    # Persist to test case if ID was provided
    if body.test_case_id:
        tc = await _get_test_or_404(db, body.test_case_id, current_user.tenant_id)
        tc.ai_business_process = result.business_process
        tc.ai_criticality_level = result.criticality_level
        tc.ai_test_case_type = result.test_case_type
        tc.ai_dependency_class = result.dependency_class
        tc.ai_automation_feasibility = result.automation_feasibility
        tc.ai_execution_frequency = result.execution_frequency
        tc.ai_confidence_scores = result.confidence_scores
        tc.ai_needs_review = result.needs_review
        tc.ai_model_version = result.model_version
        tc.ai_classified_at = now
        await db.flush()

        await log_audit(
            db, current_user.id, "ai_classify", "test_case",
            resource_id=tc.id, tenant_id=current_user.tenant_id,
            details={"model_version": result.model_version, "needs_review": result.needs_review},
        )

    return ClassificationResponse(
        test_case_id=body.test_case_id,
        business_process=ClassificationDimension(
            value=result.business_process,
            confidence=result.confidence_scores.get("business_process", 0.0),
        ),
        criticality_level=ClassificationDimension(
            value=result.criticality_level,
            confidence=result.confidence_scores.get("criticality_level", 0.0),
        ),
        test_case_type=ClassificationDimension(
            value=result.test_case_type,
            confidence=result.confidence_scores.get("test_case_type", 0.0),
        ),
        dependency_class=ClassificationDimension(
            value=result.dependency_class,
            confidence=result.confidence_scores.get("dependency_class", 0.0),
        ),
        automation_feasibility=ClassificationDimension(
            value=result.automation_feasibility,
            confidence=result.confidence_scores.get("automation_feasibility", 0.0),
        ),
        execution_frequency=ClassificationDimension(
            value=result.execution_frequency,
            confidence=result.confidence_scores.get("execution_frequency", 0.0),
        ),
        needs_review=result.needs_review,
        model_version=result.model_version,
        classified_at=now,
    )


# ── Batch Classification ────────────────────────────────


@router.post(
    "/classify/batch",
    response_model=ClassifyBatchResponse,
    dependencies=[Depends(require_permissions("tests:write"))],
)
async def classify_batch_endpoint(
    body: ClassifyBatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClassifyBatchResponse:
    """Classify multiple test cases at once (up to 100)."""
    batch_input = [
        {
            "title": tc.title,
            "description": tc.description,
            "steps": tc.steps,
        }
        for tc in body.test_cases
    ]

    results = classify_batch(batch_input)
    now = datetime.now(timezone.utc)

    # Persist results for test cases with IDs
    for req, result in zip(body.test_cases, results):
        if req.test_case_id:
            tc = await _get_test_or_none(db, req.test_case_id, current_user.tenant_id)
            if tc:
                tc.ai_business_process = result.business_process
                tc.ai_criticality_level = result.criticality_level
                tc.ai_test_case_type = result.test_case_type
                tc.ai_dependency_class = result.dependency_class
                tc.ai_automation_feasibility = result.automation_feasibility
                tc.ai_execution_frequency = result.execution_frequency
                tc.ai_confidence_scores = result.confidence_scores
                tc.ai_needs_review = result.needs_review
                tc.ai_model_version = result.model_version
                tc.ai_classified_at = now

    await db.flush()

    responses = []
    for req, result in zip(body.test_cases, results):
        responses.append(
            ClassificationResponse(
                test_case_id=req.test_case_id,
                business_process=ClassificationDimension(
                    value=result.business_process,
                    confidence=result.confidence_scores.get("business_process", 0.0),
                ),
                criticality_level=ClassificationDimension(
                    value=result.criticality_level,
                    confidence=result.confidence_scores.get("criticality_level", 0.0),
                ),
                test_case_type=ClassificationDimension(
                    value=result.test_case_type,
                    confidence=result.confidence_scores.get("test_case_type", 0.0),
                ),
                dependency_class=ClassificationDimension(
                    value=result.dependency_class,
                    confidence=result.confidence_scores.get("dependency_class", 0.0),
                ),
                automation_feasibility=ClassificationDimension(
                    value=result.automation_feasibility,
                    confidence=result.confidence_scores.get("automation_feasibility", 0.0),
                ),
                execution_frequency=ClassificationDimension(
                    value=result.execution_frequency,
                    confidence=result.confidence_scores.get("execution_frequency", 0.0),
                ),
                needs_review=result.needs_review,
                model_version=result.model_version,
                classified_at=now,
            )
        )

    review_count = sum(1 for r in results if r.needs_review)
    all_scores = [sum(r.confidence_scores.values()) / max(len(r.confidence_scores), 1) for r in results]
    avg_conf = sum(all_scores) / max(len(all_scores), 1)

    await log_audit(
        db, current_user.id, "ai_classify_batch", "test_case",
        tenant_id=current_user.tenant_id,
        details={"total": len(results), "review_required": review_count},
    )

    return ClassifyBatchResponse(
        results=responses,
        total_classified=len(results),
        review_required=review_count,
        avg_confidence=round(avg_conf, 3),
    )


# ── Feedback / Manual Override ───────────────────────────


@router.post(
    "/classify/feedback",
    response_model=ClassificationFeedbackResponse,
    status_code=201,
    dependencies=[Depends(require_permissions("tests:write"))],
)
async def submit_feedback(
    body: ClassificationFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClassificationFeedbackResponse:
    """Submit a manual correction/override for a classification dimension.

    This both updates the test case field immediately and stores the
    feedback record for future model retraining.
    """
    tc = await _get_test_or_404(db, body.test_case_id, current_user.tenant_id)

    # Apply the correction to the test case
    dimension_field = f"ai_{body.dimension}"
    if not hasattr(tc, dimension_field):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown classification dimension: {body.dimension}",
        )
    setattr(tc, dimension_field, body.corrected_value)

    # Clear the needs_review flag if all dimensions now have overrides
    tc.ai_needs_review = False

    # Store feedback record
    feedback = ClassificationFeedback(
        test_case_id=body.test_case_id,
        dimension=body.dimension,
        original_value=body.original_value,
        corrected_value=body.corrected_value,
        reason=body.reason,
        submitted_by=current_user.id,
        tenant_id=current_user.tenant_id,
        model_version=tc.ai_model_version or "unknown",
    )
    db.add(feedback)
    await db.flush()
    await db.refresh(feedback)

    await log_audit(
        db, current_user.id, "ai_classify_feedback", "test_case",
        resource_id=tc.id, tenant_id=current_user.tenant_id,
        details={
            "dimension": body.dimension,
            "original": body.original_value,
            "corrected": body.corrected_value,
        },
    )

    return ClassificationFeedbackResponse(
        id=feedback.id,
        test_case_id=feedback.test_case_id,
        dimension=feedback.dimension,
        original_value=feedback.original_value,
        corrected_value=feedback.corrected_value,
        reason=feedback.reason,
        submitted_by=feedback.submitted_by,
        submitted_at=feedback.created_at,
    )


# ── Review Queue ─────────────────────────────────────────


@router.get(
    "/classify/review-queue",
    response_model=ReviewQueueResponse,
    dependencies=[Depends(require_permissions("tests:read"))],
)
async def get_review_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewQueueResponse:
    """Get the classification review queue — test cases with low-confidence AI results."""
    query = select(TestCase).where(
        TestCase.tenant_id == current_user.tenant_id,
        TestCase.ai_needs_review.is_(True),
        TestCase.archived_at.is_(None),
    )

    # Count total
    count_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(TestCase.ai_classified_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    test_cases = result.scalars().all()

    items: list[ReviewQueueItem] = []
    for tc in test_cases:
        confidence_scores = tc.ai_confidence_scores or {}
        if confidence_scores:
            lowest_dim = min(confidence_scores, key=lambda k: confidence_scores[k])
            lowest_score = confidence_scores[lowest_dim]
        else:
            lowest_dim = "unknown"
            lowest_score = 0.0

        now = datetime.now(timezone.utc)
        classification = ClassificationResponse(
            test_case_id=tc.id,
            business_process=ClassificationDimension(
                value=tc.ai_business_process or "Unknown",
                confidence=confidence_scores.get("business_process", 0.0),
            ),
            criticality_level=ClassificationDimension(
                value=tc.ai_criticality_level or "Unknown",
                confidence=confidence_scores.get("criticality_level", 0.0),
            ),
            test_case_type=ClassificationDimension(
                value=tc.ai_test_case_type or "Unknown",
                confidence=confidence_scores.get("test_case_type", 0.0),
            ),
            dependency_class=ClassificationDimension(
                value=tc.ai_dependency_class or "Unknown",
                confidence=confidence_scores.get("dependency_class", 0.0),
            ),
            automation_feasibility=ClassificationDimension(
                value=tc.ai_automation_feasibility or "Unknown",
                confidence=confidence_scores.get("automation_feasibility", 0.0),
            ),
            execution_frequency=ClassificationDimension(
                value=tc.ai_execution_frequency or "Unknown",
                confidence=confidence_scores.get("execution_frequency", 0.0),
            ),
            needs_review=True,
            model_version=tc.ai_model_version or "unknown",
            classified_at=tc.ai_classified_at or now,
        )

        items.append(
            ReviewQueueItem(
                test_case_id=tc.id,
                title=tc.title,
                classification=classification,
                lowest_confidence_dimension=lowest_dim,
                lowest_confidence_score=lowest_score,
                created_at=tc.created_at,
            )
        )

    return ReviewQueueResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ── Helpers ──────────────────────────────────────────────


def _steps_to_text(steps: list | dict | None) -> Optional[str]:
    """Convert structured steps JSON to plain text for classification."""
    if not steps:
        return None
    if isinstance(steps, list):
        parts = []
        for s in steps:
            if isinstance(s, dict):
                action = s.get("action", s.get("step", ""))
                expected = s.get("expected", s.get("expected_result", ""))
                parts.append(f"{action} {expected}".strip())
            else:
                parts.append(str(s))
        return " ".join(parts)
    return str(steps)


async def _get_test_or_404(
    db: AsyncSession, test_id: UUID, tenant_id: UUID
) -> TestCase:
    result = await db.execute(
        select(TestCase).where(TestCase.id == test_id, TestCase.tenant_id == tenant_id)
    )
    tc = result.scalar_one_or_none()
    if tc is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    return tc


async def _get_test_or_none(
    db: AsyncSession, test_id: UUID, tenant_id: UUID
) -> Optional[TestCase]:
    result = await db.execute(
        select(TestCase).where(TestCase.id == test_id, TestCase.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()
