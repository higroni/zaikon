"""Evaluation harness endpoints."""

from fastapi import APIRouter

from zaikon.modules.evaluation.schemas import EvaluationCase, EvaluationRunResponse
from zaikon.modules.evaluation.service import get_evaluation_service

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.get("/gold-cases", response_model=list[EvaluationCase])
def list_gold_cases() -> list[EvaluationCase]:
    """List all gold test cases for evaluation."""
    return get_evaluation_service().list_cases()


@router.get("/cases", response_model=list[EvaluationCase])
def list_evaluation_cases() -> list[EvaluationCase]:
    """Deprecated: Use /gold-cases instead."""
    return get_evaluation_service().list_cases()


@router.post("/run", response_model=EvaluationRunResponse)
def run_evaluation() -> EvaluationRunResponse:
    return get_evaluation_service().run()
