"""Finding endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from zaikon.modules.checkers.schemas import (
    FindingRecord,
    UpdateFindingReviewDecisionRequest,
    UpdateFindingReviewDecisionResponse,
)
from zaikon.modules.draft_reviews.service import get_draft_review_service

router = APIRouter(prefix="/findings", tags=["findings"])


@router.get("/{finding_id}", response_model=FindingRecord)
def get_finding(finding_id: UUID) -> FindingRecord:
    finding = get_draft_review_service().get_finding(finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.patch(
    "/{finding_id}/review-decision",
    response_model=UpdateFindingReviewDecisionResponse,
)
def update_finding_review_decision(
    finding_id: UUID,
    request: UpdateFindingReviewDecisionRequest,
) -> UpdateFindingReviewDecisionResponse:
    finding = get_draft_review_service().update_finding_review_decision(
        finding_id=finding_id,
        status=request.status,
        review_note=request.review_note,
    )
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return UpdateFindingReviewDecisionResponse(finding=finding)

