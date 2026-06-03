"""Draft review endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from typing import Any

from zaikon.modules.assertions.schemas import NormativeAssertion
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


@router.get("/{pipeline_run_id}/akoma-ntoso")
def export_draft_review_akoma_ntoso(pipeline_run_id: UUID) -> Response:
    xml_text = get_draft_review_service().export_akoma_ntoso(pipeline_run_id)
    if xml_text is None:
        raise HTTPException(
            status_code=404,
            detail="Draft review Akoma Ntoso artifact not found",
        )
    return Response(content=xml_text, media_type="application/xml")


@router.get("/{pipeline_run_id}/artifacts", response_model=list[str])
def list_draft_review_artifacts(pipeline_run_id: UUID) -> list[str]:
    artifacts = get_draft_review_service().list_artifacts(pipeline_run_id)
    if artifacts is None:
        raise HTTPException(status_code=404, detail="Draft review not found")
    return artifacts


@router.get("/{pipeline_run_id}/artifacts/{artifact_name}")
def get_draft_review_artifact(
    pipeline_run_id: UUID,
    artifact_name: str,
) -> dict[str, Any] | list[Any] | str | int | float | bool | None:
    artifact = get_draft_review_service().get_artifact(
        pipeline_run_id=pipeline_run_id,
        artifact_name=artifact_name,
    )
    if artifact is None:
        raise HTTPException(status_code=404, detail="Draft review artifact not found")
    return artifact


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


@router.get("/{pipeline_run_id}/assertions", response_model=list[NormativeAssertion])
def list_assertions(pipeline_run_id: UUID) -> list[NormativeAssertion]:
    assertions = get_draft_review_service().list_assertions(pipeline_run_id)
    if assertions is None:
        raise HTTPException(status_code=404, detail="Draft review not found")
    return assertions


@router.get("/{pipeline_run_id}/conflict-candidates")
def list_conflict_candidates(pipeline_run_id: UUID) -> list[Any]:
    candidates = get_draft_review_service().get_artifact(
        pipeline_run_id=pipeline_run_id,
        artifact_name="conflict_candidates",
    )
    if candidates is None:
        raise HTTPException(status_code=404, detail="Conflict candidates not found")
    return candidates


@router.get("/{pipeline_run_id}/conflict-trace")
def get_conflict_trace(pipeline_run_id: UUID) -> dict[str, Any]:
    trace = get_draft_review_service().get_artifact(
        pipeline_run_id=pipeline_run_id,
        artifact_name="conflict_trace",
    )
    if trace is None:
        raise HTTPException(status_code=404, detail="Conflict trace not found")
    return trace
