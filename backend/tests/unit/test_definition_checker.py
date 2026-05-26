"""Unit tests for definition consistency checker."""

from uuid import uuid4

from zaikon.modules.canonical.schemas import CanonicalDocument
from zaikon.modules.checkers.service import DefinitionConsistencyChecker


def test_definition_consistency_checker_reports_conflicting_definitions():
    pipeline_run_id = uuid4()
    document = CanonicalDocument(
        source_uri="draft-review://test",
        filename="nacrt.txt",
        document_type="law",
        canonical_json={
            "schema_version": "0.1",
            "document": {},
            "legal_units": [
                {
                    "legal_unit_id": "unit-1",
                    "path": "article:1/paragraph:1",
                    "content_text": (
                        "Ministarstvo nadlezno za poslove suma "
                        "(u daljem tekstu: Ministarstvo)."
                    ),
                },
                {
                    "legal_unit_id": "unit-2",
                    "path": "article:2/paragraph:1",
                    "content_text": (
                        "Ministarstvo nadlezno za finansije "
                        "(u daljem tekstu: Ministarstvo)."
                    ),
                },
            ],
            "metadata": {},
        },
    )

    findings = DefinitionConsistencyChecker().check(
        pipeline_run_id=pipeline_run_id,
        document=document,
    )

    assert len(findings) == 1
    assert findings[0].finding_type == "definition_conflict"
    assert findings[0].risk_level == "medium"
    assert findings[0].evidence["term"] == "Ministarstvo"
    assert len(findings[0].evidence["definitions"]) == 2


def test_definition_consistency_checker_ignores_repeated_same_definition():
    pipeline_run_id = uuid4()
    document = CanonicalDocument(
        source_uri="draft-review://test",
        filename="nacrt.txt",
        document_type="law",
        canonical_json={
            "schema_version": "0.1",
            "document": {},
            "legal_units": [
                {
                    "legal_unit_id": "unit-1",
                    "path": "article:1/paragraph:1",
                    "content_text": (
                        "Nadlezni organ (u daljem tekstu: Organ). "
                        "Nadlezni organ (u daljem tekstu: Organ)."
                    ),
                }
            ],
            "metadata": {},
        },
    )

    findings = DefinitionConsistencyChecker().check(
        pipeline_run_id=pipeline_run_id,
        document=document,
    )

    assert findings == []
