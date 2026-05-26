"""Unit tests for reference extraction."""

from zaikon.modules.canonical.schemas import CanonicalDocument
from zaikon.modules.references.schemas import ExtractReferencesRequest
from zaikon.modules.references.schemas import ResolveReferencesRequest
from zaikon.modules.references.service import ReferenceService


def test_reference_service_extracts_article_and_official_gazette_references():
    document = CanonicalDocument(
        source_uri="file:///tmp/zakon.txt",
        filename="zakon.txt",
        document_type="law",
        title="Zakon o primerima",
        canonical_json={
            "schema_version": "0.1",
            "document": {},
            "legal_units": [
                {
                    "legal_unit_id": "unit-1",
                    "path": "article:1/paragraph:1",
                    "content_text": (
                        "U skladu sa clanom 5. stav 2. tacka 1. ovog zakona "
                        "i Sluzbeni glasnik RS, broj 30/10."
                    ),
                }
            ],
            "metadata": {},
        },
    )

    response = ReferenceService().extract_references(
        ExtractReferencesRequest(document=document)
    )

    assert len(response.references) == 2
    article_reference = response.references[0]
    gazette_reference = response.references[1]
    assert article_reference.reference_type == "article_reference"
    assert article_reference.target_article_number == "5"
    assert article_reference.target_paragraph_number == "2"
    assert article_reference.target_item_number == "1"
    assert article_reference.source_path == "article:1/paragraph:1"
    assert gazette_reference.reference_type == "official_gazette_reference"
    assert gazette_reference.target_document_title == "Sluzbeni glasnik RS"


def test_reference_service_resolves_internal_article_references():
    document = CanonicalDocument(
        source_uri="file:///tmp/zakon.txt",
        filename="zakon.txt",
        document_type="law",
        canonical_json={
            "schema_version": "0.1",
            "document": {},
            "legal_units": [
                {
                    "legal_unit_id": "article-5",
                    "path": "article:5",
                    "content_text": "Clan 5.",
                },
                {
                    "legal_unit_id": "paragraph-5-2",
                    "parent_legal_unit_id": "article-5",
                    "path": "article:5/paragraph:2",
                    "content_text": "Drugi stav.",
                },
                {
                    "legal_unit_id": "article-1",
                    "path": "article:1",
                    "content_text": "Upucuje se na clan 5. stav 2. i clan 99.",
                },
            ],
            "metadata": {},
        },
    )
    service = ReferenceService()
    extracted = service.extract_references(ExtractReferencesRequest(document=document))

    response = service.resolve_references(
        ResolveReferencesRequest(references=extracted.references, document=document)
    )

    statuses = [item.resolution_status for item in response.resolved_references]
    assert statuses == ["resolved", "missing"]
    assert response.resolved_references[0].target_legal_unit_id == "paragraph-5-2"


def test_reference_service_resolves_internal_item_references():
    document = CanonicalDocument(
        source_uri="file:///tmp/zakon.txt",
        filename="zakon.txt",
        document_type="law",
        canonical_json={
            "schema_version": "0.1",
            "document": {},
            "legal_units": [
                {
                    "legal_unit_id": "article-5",
                    "unit_type": "article",
                    "path": "article:5",
                    "content_text": "",
                },
                {
                    "legal_unit_id": "paragraph-5-2",
                    "unit_type": "paragraph",
                    "parent_legal_unit_id": "article-5",
                    "path": "article:5/paragraph:2",
                    "content_text": "",
                },
                {
                    "legal_unit_id": "item-5-2-1",
                    "unit_type": "item",
                    "parent_legal_unit_id": "paragraph-5-2",
                    "path": "article:5/paragraph:2/item:1",
                    "content_text": "Prva tacka.",
                },
                {
                    "legal_unit_id": "paragraph-1-1",
                    "unit_type": "paragraph",
                    "path": "article:1/paragraph:1",
                    "content_text": "Upucuje se na clan 5. stav 2. tacka 1.",
                },
            ],
            "metadata": {},
        },
    )
    service = ReferenceService()
    extracted = service.extract_references(ExtractReferencesRequest(document=document))

    response = service.resolve_references(
        ResolveReferencesRequest(references=extracted.references, document=document)
    )

    assert len(response.resolved_references) == 1
    assert response.resolved_references[0].resolution_status == "resolved"
    assert response.resolved_references[0].target_legal_unit_id == "item-5-2-1"


def test_reference_service_keeps_paragraph_references_when_paragraph_has_items():
    document = CanonicalDocument(
        source_uri="file:///tmp/zakon.txt",
        filename="zakon.txt",
        document_type="law",
        canonical_json={
            "schema_version": "0.1",
            "document": {},
            "legal_units": [
                {
                    "legal_unit_id": "paragraph-1-1",
                    "unit_type": "paragraph",
                    "path": "article:1/paragraph:1",
                    "content_text": "Preambula upucuje na clan 5. 1) prva tacka.",
                },
                {
                    "legal_unit_id": "item-1-1-1",
                    "unit_type": "item",
                    "parent_legal_unit_id": "paragraph-1-1",
                    "path": "article:1/paragraph:1/item:1",
                    "content_text": "prva tacka.",
                },
            ],
            "metadata": {},
        },
    )

    response = ReferenceService().extract_references(
        ExtractReferencesRequest(document=document)
    )

    assert len(response.references) == 1
    assert response.references[0].source_path == "article:1/paragraph:1"


def test_reference_service_resolves_cross_document_article_reference():
    draft = CanonicalDocument(
        source_uri="draft-review://test",
        filename="nacrt.txt",
        document_type="law",
        title="Nacrt zakona",
        canonical_json={
            "schema_version": "0.1",
            "document": {},
            "legal_units": [
                {
                    "legal_unit_id": "draft-paragraph-1",
                    "unit_type": "paragraph",
                    "path": "article:1/paragraph:1",
                    "content_text": "Postupak se sprovodi u skladu sa članom 5. Zakona o šumama.",
                }
            ],
            "metadata": {},
        },
    )
    corpus_document = CanonicalDocument(
        source_uri="file:///tmp/zakon-o-sumama.txt",
        filename="zakon-o-sumama.txt",
        document_type="law",
        title="Zakon o šumama",
        canonical_json={
            "schema_version": "0.1",
            "document": {},
            "legal_units": [
                {
                    "legal_unit_id": "forest-article-5",
                    "unit_type": "article",
                    "path": "article:5",
                    "content_text": "Član 5.",
                }
            ],
            "metadata": {},
        },
    )
    service = ReferenceService()
    extracted = service.extract_references(ExtractReferencesRequest(document=draft))

    response = service.resolve_references(
        ResolveReferencesRequest(
            references=extracted.references,
            document=draft,
            corpus_documents=[corpus_document],
        )
    )

    assert len(extracted.references) == 1
    assert extracted.references[0].target_document_title == "Zakon o šumama"
    assert response.resolved_references[0].resolution_status == "resolved"
    assert response.resolved_references[0].target_legal_unit_id == "forest-article-5"
    assert "Zakon o šumama" in response.resolved_references[0].resolution_note
