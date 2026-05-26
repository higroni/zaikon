"""Unit tests for terminology and temporal validity checkers."""

from uuid import uuid4

from zaikon.modules.canonical.schemas import CanonicalDocument
from zaikon.modules.checkers.service import (
    TemporalValidityChecker,
    TerminologyConsistencyChecker,
)


def _document(content_text: str) -> CanonicalDocument:
    return CanonicalDocument(
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
                    "content_text": content_text,
                }
            ],
            "metadata": {},
        },
    )


def test_terminology_checker_reports_vague_institutional_term():
    findings = TerminologyConsistencyChecker().check(
        pipeline_run_id=uuid4(),
        document=_document("Nadlezni organ vodi evidenciju."),
    )

    assert len(findings) == 1
    assert findings[0].finding_type == "terminology_inconsistent"
    assert findings[0].risk_level == "low"
    assert findings[0].evidence["matched_terms"] == ["nadlezni organ"]


def test_temporal_validity_checker_reports_impossible_date():
    findings = TemporalValidityChecker().check(
        pipeline_run_id=uuid4(),
        document=_document("Ovaj zakon primenjuje se od 31. februar 2026."),
    )

    assert len(findings) == 1
    assert findings[0].finding_type == "temporal_validity_issue"
    assert findings[0].risk_level == "medium"
    assert findings[0].evidence["invalid_dates"] == ["31. februar 2026"]
