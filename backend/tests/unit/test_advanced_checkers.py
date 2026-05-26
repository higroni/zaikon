"""Unit tests for advanced deterministic checker skeletons."""

from uuid import uuid4

from zaikon.modules.canonical.schemas import CanonicalDocument
from zaikon.modules.checkers.service import (
    NormConflictChecker,
    OverlapChecker,
    StaleReferenceChecker,
)


def _document(units: list[dict]) -> CanonicalDocument:
    return CanonicalDocument(
        source_uri="draft-review://test",
        filename="nacrt.txt",
        document_type="law",
        canonical_json={
            "schema_version": "0.1",
            "document": {},
            "legal_units": units,
            "metadata": {},
        },
    )


def test_norm_conflict_checker_flags_obligation_and_prohibition():
    findings = NormConflictChecker().check(
        pipeline_run_id=uuid4(),
        document=_document(
            [
                {
                    "legal_unit_id": "unit-1",
                    "path": "article:1/paragraph:1",
                    "content_text": "Organ mora da postupi, ali ne sme da izda odobrenje.",
                }
            ]
        ),
    )

    assert len(findings) == 1
    assert findings[0].finding_type == "possible_norm_conflict"


def test_overlap_checker_flags_repeated_wording():
    repeated = "Organ vodi evidenciju o korisnicima sredstava i merama zastite."
    findings = OverlapChecker().check(
        pipeline_run_id=uuid4(),
        document=_document(
            [
                {
                    "legal_unit_id": "unit-1",
                    "path": "article:1/paragraph:1",
                    "content_text": repeated,
                },
                {
                    "legal_unit_id": "unit-2",
                    "path": "article:2/paragraph:1",
                    "content_text": repeated,
                },
            ]
        ),
    )

    assert len(findings) == 1
    assert findings[0].finding_type == "possible_overlap"
    assert findings[0].evidence["duplicate_of_path"] == "article:1/paragraph:1"


def test_stale_reference_checker_flags_repeal_language():
    findings = StaleReferenceChecker().check(
        pipeline_run_id=uuid4(),
        document=_document(
            [
                {
                    "legal_unit_id": "unit-1",
                    "path": "article:1/paragraph:1",
                    "content_text": "Danom stupanja na snagu ovog zakona prestaje da vazi raniji pravilnik.",
                }
            ]
        ),
    )

    assert len(findings) == 1
    assert findings[0].finding_type == "reference_stale"
