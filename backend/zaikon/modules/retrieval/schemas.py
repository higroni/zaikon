"""Retrieval module schemas."""

from pydantic import BaseModel, Field


class RetrievalResult(BaseModel):
    document_id: str
    legal_unit_id: str
    document_type: str
    filename: str
    unit_type: str
    path: str
    content_text: str
    score: float
    metadata: dict = Field(default_factory=dict)


class HybridSearchRequest(BaseModel):
    query: str
    top_k: int = 10


class HybridSearchResponse(BaseModel):
    results: list[RetrievalResult] = Field(default_factory=list)


class RetrieveForLegalUnitRequest(BaseModel):
    query: str
    top_k: int = 10


class RetrieveForLegalUnitResponse(BaseModel):
    results: list[RetrievalResult] = Field(default_factory=list)
