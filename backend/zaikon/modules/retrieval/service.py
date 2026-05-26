"""Deterministic hybrid retrieval over persisted legal units."""

from functools import lru_cache
import re

from zaikon.modules.documents.catalog import DocumentCatalogService
from zaikon.modules.indexing.embeddings import (
    cosine_similarity,
    deterministic_embedding,
    tokens,
)
from zaikon.modules.retrieval.schemas import (
    HybridSearchRequest,
    HybridSearchResponse,
    RetrievalResult,
    RetrieveForLegalUnitRequest,
    RetrieveForLegalUnitResponse,
)


def _tokens(value: str) -> set[str]:
    return set(tokens(value))


def _raw_tokens(value: str) -> set[str]:
    return {token.lower() for token in re.findall(r"\w+", value) if len(token) >= 3}


class RetrievalService:
    """Hybrid lexical plus deterministic semantic fallback retrieval."""

    def __init__(self, catalog: DocumentCatalogService | None = None) -> None:
        self.catalog = catalog or DocumentCatalogService()

    def hybrid_search(self, request: HybridSearchRequest) -> HybridSearchResponse:
        return HybridSearchResponse(
            results=self._search(
                query=request.query,
                top_k=request.top_k,
                corpus_id=str(request.corpus_id) if request.corpus_id else None,
            )
        )

    def retrieve_for_legal_unit(
        self, request: RetrieveForLegalUnitRequest
    ) -> RetrieveForLegalUnitResponse:
        return RetrieveForLegalUnitResponse(
            results=self._search(
                query=request.query,
                top_k=request.top_k,
                corpus_id=str(request.corpus_id) if request.corpus_id else None,
            )
        )

    def _search(
        self, query: str, top_k: int, corpus_id: str | None = None
    ) -> list[RetrievalResult]:
        query_tokens = _tokens(query)
        raw_query_tokens = _raw_tokens(query)
        query_vector = deterministic_embedding(query)
        if not query_tokens and not any(query_vector):
            return []

        results = []
        for document in self.catalog.list_documents():
            if corpus_id and str(document.corpus_id) != corpus_id:
                continue
            detail = self.catalog.get_document(document.document_id)
            if detail is None:
                continue
            for unit in detail.canonical_json.get("legal_units", []):
                content_text = unit.get("content_text") or ""
                content_tokens = _tokens(content_text)
                matches = query_tokens & content_tokens
                raw_matches = raw_query_tokens & _raw_tokens(content_text)
                lexical_score = (
                    len(matches) / len(query_tokens) if query_tokens else 0.0
                )
                semantic_score = cosine_similarity(
                    query_vector,
                    deterministic_embedding(content_text),
                )
                score = 0.65 * lexical_score + 0.35 * semantic_score
                if score <= 0:
                    continue
                results.append(
                    RetrievalResult(
                        document_id=str(document.document_id),
                        corpus_id=str(document.corpus_id)
                        if document.corpus_id is not None
                        else None,
                        legal_unit_id=unit["legal_unit_id"],
                        document_type=document.document_type,
                        filename=document.filename,
                        unit_type=unit["unit_type"],
                        path=unit["path"],
                        content_text=content_text,
                        score=score,
                        metadata={
                            "matched_terms": sorted(matches | raw_matches),
                            "lexical_score": lexical_score,
                            "semantic_score": semantic_score,
                            "retrieval_mode": "hybrid_deterministic",
                        },
                    )
                )

        results.sort(key=lambda item: item.score, reverse=True)
        return results[:top_k]


@lru_cache
def get_retrieval_service() -> RetrievalService:
    return RetrievalService()
