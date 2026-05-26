"""Indexing module request and response schemas."""

from typing import Any

from pydantic import BaseModel, Field

from zaikon.modules.canonical.schemas import CanonicalDocument


class BuildIndexesRequest(BaseModel):
    documents: list[CanonicalDocument]
    resolved_references: list[dict[str, Any]] = Field(default_factory=list)


class IndexReport(BaseModel):
    index_name: str
    status: str = "completed"
    indexed_documents: int = 0
    indexed_legal_units: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class BuildIndexesResponse(BaseModel):
    keyword_index_report: IndexReport
    vector_index_report: IndexReport
    structure_index_report: IndexReport
    reference_graph_report: IndexReport


class RefreshIndexesRequest(BaseModel):
    documents: list[CanonicalDocument]


class RefreshIndexesResponse(BaseModel):
    reports: list[IndexReport] = Field(default_factory=list)
