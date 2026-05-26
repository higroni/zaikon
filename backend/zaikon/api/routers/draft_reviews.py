"""Draft review endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from zaikon.modules.checkers.schemas import FindingRecord
from zaikon.modules.draft_reviews.schemas import (
    CreateDraftReviewFromFileRequest,
    CreateDraftReviewRequest,
    CreateDraftReviewResponse,
    DraftReviewDetail,
    DraftReviewRecord,
    RunDraftReviewResponse,
)
from zaikon.modules.draft_reviews.service import get_draft_review_service

router = APIRouter(prefix="/draft-reviews", tags=["draft-reviews"])


@router.post("", response_model=CreateDraftReviewResponse)
def create_draft_review(
    request: CreateDraftReviewRequest,
) -> CreateDraftReviewResponse:
    return get_draft_review_service().create_draft_review(request)


@router.post("/from-file", response_model=CreateDraftReviewResponse)
def create_draft_review_from_file(
    request: CreateDraftReviewFromFileRequest,
) -> CreateDraftReviewResponse:
    try:
        return get_draft_review_service().create_draft_review_from_file(request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[DraftReviewRecord])
def list_draft_reviews() -> list[DraftReviewRecord]:
    return get_draft_review_service().list_draft_reviews()


@router.get("/{pipeline_run_id}", response_model=DraftReviewDetail)
def get_draft_review(pipeline_run_id: UUID) -> DraftReviewDetail:
    detail = get_draft_review_service().get_draft_review(pipeline_run_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Draft review not found")
    return detail


@router.post("/{pipeline_run_id}/run", response_model=RunDraftReviewResponse)
def run_draft_review(pipeline_run_id: UUID) -> RunDraftReviewResponse:
    try:
        return get_draft_review_service().run_draft_review(pipeline_run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{pipeline_run_id}/findings", response_model=list[FindingRecord])
def list_findings(pipeline_run_id: UUID) -> list[FindingRecord]:
    detail = get_draft_review_service().get_draft_review(pipeline_run_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Draft review not found")
    return detail.findings
