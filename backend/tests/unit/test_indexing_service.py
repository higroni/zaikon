"""Unit tests for indexing reports."""

from zaikon.modules.canonical.schemas import CanonicalDocument
from zaikon.modules.indexing.schemas import BuildIndexesRequest
from zaikon.modules.indexing.service import IndexingService


def test_indexing_service_builds_deterministic_reports():
    document = CanonicalDocument(
        source_uri="file:///tmp/zakon.txt",
        filename="zakon.txt",
        document_type="law",
        canonical_json={
            "schema_version": "0.1",
            "document": {},
            "legal_units": [
                {
                    "unit_type": "article",
                    "content_text": "Sume i sumarsko zemljiste su dobro od interesa.",
                },
                {
                    "unit_type": "paragraph",
                    "content_text": "Sume se stite i koriste odrzivo.",
                },
            ],
            "metadata": {},
        },
    )

    response = IndexingService().build_indexes(
        BuildIndexesRequest(
            documents=[document],
            resolved_references=[
                {
                    "metadata": {
                        "resolved_count": 1,
                        "missing_count": 2,
                        "out_of_scope_count": 3,
                    }
                }
            ],
        )
    )

    assert response.keyword_index_report.indexed_documents == 1
    assert response.keyword_index_report.indexed_legal_units == 2
    assert response.keyword_index_report.metadata["unique_terms"] > 0
    assert response.structure_index_report.metadata["document_types"] == {"law": 1}
    assert response.reference_graph_report.metadata == {
        "resolved_references": 1,
        "missing_references": 2,
        "out_of_scope_references": 3,
    }
