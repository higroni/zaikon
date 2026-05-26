"""Indexing report service for early corpus import MVP."""

from collections import Counter
from functools import lru_cache
import re

from zaikon.core.config import settings
from zaikon.core.schemas import ModuleHealth
from zaikon.modules.indexing.schemas import (
    BuildIndexesRequest,
    BuildIndexesResponse,
    IndexReport,
    RefreshIndexesRequest,
    RefreshIndexesResponse,
)


class IndexingService:
    """Builds deterministic index reports without external storage."""

    def health(self) -> ModuleHealth:
        return ModuleHealth(module_name="indexing")

    def build_indexes(self, request: BuildIndexesRequest) -> BuildIndexesResponse:
        legal_units = [
            unit
            for document in request.documents
            for unit in document.canonical_json.get("legal_units", [])
        ]
        document_types = Counter(document.document_type for document in request.documents)
        tokens = Counter()
        for unit in legal_units:
            tokens.update(
                token
                for token in re.findall(r"[A-Za-zČĆŠĐŽčćšđž0-9]+", unit.get("content_text") or "")
                if len(token) >= 3
            )

        resolved_count = 0
        missing_count = 0
        out_of_scope_count = 0
        for document in request.resolved_references:
            metadata = document.get("metadata", {})
            resolved_count += metadata.get("resolved_count", 0)
            missing_count += metadata.get("missing_count", 0)
            out_of_scope_count += metadata.get("out_of_scope_count", 0)

        common = {
            "indexed_documents": len(request.documents),
            "indexed_legal_units": len(legal_units),
        }
        return BuildIndexesResponse(
            keyword_index_report=IndexReport(
                index_name="keyword",
                **common,
                metadata={
                    "backend": settings.keyword_backend,
                    "unique_terms": len(tokens),
                    "top_terms": [
                        {"term": term, "count": count}
                        for term, count in tokens.most_common(10)
                    ],
                },
            ),
            vector_index_report=IndexReport(
                index_name="vector",
                **common,
                metadata={
                    "backend": settings.vector_backend,
                    "embedding_model": settings.embedding_model,
                    "embedding_dimensions": settings.embedding_dimensions,
                    "status_note": "report_only_no_embeddings_computed",
                },
            ),
            structure_index_report=IndexReport(
                index_name="structure",
                **common,
                metadata={
                    "document_types": dict(document_types),
                    "unit_types": dict(Counter(unit.get("unit_type") for unit in legal_units)),
                },
            ),
            reference_graph_report=IndexReport(
                index_name="reference_graph",
                **common,
                metadata={
                    "resolved_references": resolved_count,
                    "missing_references": missing_count,
                    "out_of_scope_references": out_of_scope_count,
                },
            ),
        )

    def refresh_indexes(
        self, request: RefreshIndexesRequest
    ) -> RefreshIndexesResponse:
        response = self.build_indexes(BuildIndexesRequest(documents=request.documents))
        return RefreshIndexesResponse(
            reports=[
                response.keyword_index_report,
                response.vector_index_report,
                response.structure_index_report,
                response.reference_graph_report,
            ]
        )


@lru_cache
def get_indexing_service() -> IndexingService:
    return IndexingService()
