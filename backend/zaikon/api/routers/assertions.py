"""Normative assertion endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from zaikon.modules.assertions.schemas import NormativeAssertion
from zaikon.modules.draft_reviews.service import get_draft_review_service

router = APIRouter(prefix="/assertions", tags=["assertions"])


@router.get("/draft-reviews/{pipeline_run_id}", response_model=list[NormativeAssertion])
def list_draft_review_assertions(pipeline_run_id: UUID) -> list[NormativeAssertion]:
    assertions = get_draft_review_service().list_assertions(pipeline_run_id)
    if assertions is None:
        raise HTTPException(status_code=404, detail="Draft review not found")
    return assertions
