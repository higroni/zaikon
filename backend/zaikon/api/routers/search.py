"""Search endpoints."""

from fastapi import APIRouter

from zaikon.modules.retrieval.schemas import (
    HybridSearchRequest,
    HybridSearchResponse,
    RetrieveForLegalUnitRequest,
    RetrieveForLegalUnitResponse,
)
from zaikon.modules.retrieval.service import get_retrieval_service

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/hybrid", response_model=HybridSearchResponse)
def hybrid_search(request: HybridSearchRequest) -> HybridSearchResponse:
    return get_retrieval_service().hybrid_search(request)


@router.post("/legal-unit", response_model=RetrieveForLegalUnitResponse)
def retrieve_for_legal_unit(
    request: RetrieveForLegalUnitRequest,
) -> RetrieveForLegalUnitResponse:
    return get_retrieval_service().retrieve_for_legal_unit(request)
