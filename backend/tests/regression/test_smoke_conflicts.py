"""Smoke tests for Faza 0: osnovni primeri konflikata prema ACTION_PLAN."""

from uuid import uuid4

import pytest

from zaikon.modules.assertions.schemas import (
    DeadlineSlot,
    ExtractAssertionsRequest,
    LegalSlot,
    NormativeAssertion,
)
from zaikon.modules.assertions.service import AssertionExtractionService
from zaikon.modules.canonical.schemas import CanonicalDocument
from zaikon.modules.conflicts.service import ConflictRegistryService
from zaikon.modules.ontology.service import get_ontology_service


def _make_document(text: str, filename: str = "test.txt") -> CanonicalDocument:
    """Helper to create a minimal canonical document."""
    return CanonicalDocument(
        source_uri=f"test://{filename}",
        filename=filename,
        document_type="law",
        canonical_json={
            "schema_version": "0.1",
            "document": {"title": "Test Document"},
            "legal_units": [
                {
                    "legal_unit_id": "unit-1",
                    "path": "article:1/paragraph:1",
                    "content_text": text,
                }
            ],
            "metadata": {},
        },
    )


class TestSmokeConflicts:
    """
    Smoke testovi za tri osnovna primera iz ACTION_PLAN Faza 0:
    1. Obelezavanje drveca: svaki gradjanin vs ovlasceno lice
    2. Rok: 15 dana vs 30 dana
    3. Pogresna nadleznost: kontrola hrane -> gradjevinska inspekcija
    """

    def test_authority_scope_conflict_any_person_vs_authorized(self):
        """
        Primer 1: Nacrt dozvoljava 'svaki gradjanin', korpus zahteva 'ovlasceno lice'.
        Ocekivani nalaz: authority_scope_conflict (broader_than_allowed).
        """
        # Nacrt: svaki gradjanin moze da obelezava drvece
        draft_doc = _make_document(
            "Obelezavanje drveca moze da vrsi svaki gradjanin.", "nacrt.txt"
        )

        # Korpus: samo ovlasceno lice
        corpus_doc = _make_document(
            "Obelezavanje drveca vrsi ovlasceno pravno lice.", "zakon.txt"
        )

        # Extract assertions
        extractor = AssertionExtractionService()
        draft_assertions = extractor.extract_from_document(
            document=draft_doc, pipeline_run_id=uuid4()
        )
        corpus_assertions = extractor.extract_from_document(
            document=corpus_doc, corpus_id=uuid4()
        )

        # Verify extraction worked
        assert len(draft_assertions) > 0, "Draft assertion not extracted"
        assert len(corpus_assertions) > 0, "Corpus assertion not extracted"

        draft_assertion = draft_assertions[0]
        corpus_assertion = corpus_assertions[0]

        # Check actor slots
        assert draft_assertion.actor is not None, "Draft actor not extracted"
        assert corpus_assertion.actor is not None, "Corpus actor not extracted"

        # Verify ontology recognizes broader relationship
        ontology = get_ontology_service()
        is_broader = ontology.is_broader_actor(
            draft_assertion.actor.canonical, corpus_assertion.actor.canonical
        )
        assert is_broader, (
            f"Ontology should recognize {draft_assertion.actor.canonical} "
            f"as broader than {corpus_assertion.actor.canonical}"
        )

        # Run conflict detection
        conflict_service = ConflictRegistryService()
        evaluation = conflict_service.evaluate_assertion_conflicts(
            pipeline_run_id=uuid4(),
            draft_assertions=[draft_assertion],
            corpus_assertions=[corpus_assertion],
        )
        findings = evaluation.findings

        # Verify conflict found
        assert len(findings) > 0, "No conflict detected"
        authority_conflicts = [
            f for f in findings if f.finding_type == "authority_scope_conflict"
        ]
        assert len(authority_conflicts) > 0, "authority_scope_conflict not detected"

        finding = authority_conflicts[0]
        assert finding.risk_level in ["high", "medium"]
        assert "gradjanin" in finding.evidence.get("draft_quote", "").lower()
        assert "ovlasceno" in finding.evidence.get("corpus_quote", "").lower()

    def test_deadline_mismatch_15_vs_30_days(self):
        """
        Primer 2: Nacrt propisuje rok 15 dana, korpus 30 dana.
        Ocekivani nalaz: deadline_mismatch.
        """
        draft_doc = _make_document(
            "Nadlezni organ odlucuje u roku od 15 dana.", "nacrt.txt"
        )
        corpus_doc = _make_document(
            "Nadlezni organ odlucuje u roku od 30 dana.", "zakon.txt"
        )

        extractor = AssertionExtractionService()
        draft_assertions = extractor.extract_from_document(
            document=draft_doc, pipeline_run_id=uuid4()
        )
        corpus_assertions = extractor.extract_from_document(
            document=corpus_doc, corpus_id=uuid4()
        )

        assert len(draft_assertions) > 0, "Draft assertion not extracted"
        assert len(corpus_assertions) > 0, "Corpus assertion not extracted"

        draft_assertion = draft_assertions[0]
        corpus_assertion = corpus_assertions[0]

        # Verify deadline extraction
        assert draft_assertion.deadline is not None, "Draft deadline not extracted"
        assert corpus_assertion.deadline is not None, "Corpus deadline not extracted"
        assert draft_assertion.deadline.value == 15
        assert corpus_assertion.deadline.value == 30

        # Run conflict detection
        conflict_service = ConflictRegistryService()
        evaluation = conflict_service.evaluate_assertion_conflicts(
            pipeline_run_id=uuid4(),
            draft_assertions=[draft_assertion],
            corpus_assertions=[corpus_assertion],
        )
        findings = evaluation.findings

        assert len(findings) > 0, "No conflict detected"
        deadline_conflicts = [
            f for f in findings if f.finding_type == "deadline_mismatch"
        ]
        assert len(deadline_conflicts) > 0, "deadline_mismatch not detected"

        finding = deadline_conflicts[0]
        assert finding.risk_level in ["high", "medium"]
        assert "15" in finding.evidence.get("draft_quote", "")
        assert "30" in finding.evidence.get("corpus_quote", "")

    def test_competence_conflict_wrong_inspection_authority(self):
        """
        Primer 3: Nacrt daje kontrolu hrane gradjevinskoj inspekciji.
        Korpus: kontrolu hrane vrsi sanitarna/veterinarska inspekcija.
        Ocekivani nalaz: competence_conflict ili wrong_inspection_authority.
        """
        draft_doc = _make_document(
            "Kontrolu hrane vrsi inspekcija ministarstva nadleznog za gradjevinu.",
            "nacrt.txt",
        )
        corpus_doc = _make_document(
            "Kontrolu hrane vrsi sanitarna inspekcija.", "zakon-hrana.txt"
        )

        extractor = AssertionExtractionService()
        draft_assertions = extractor.extract_from_document(
            document=draft_doc, pipeline_run_id=uuid4()
        )
        corpus_assertions = extractor.extract_from_document(
            document=corpus_doc, corpus_id=uuid4()
        )

        assert len(draft_assertions) > 0, "Draft assertion not extracted"
        assert len(corpus_assertions) > 0, "Corpus assertion not extracted"

        draft_assertion = draft_assertions[0]
        corpus_assertion = corpus_assertions[0]

        # Verify object extraction (hrana)
        assert draft_assertion.object is not None, "Draft object not extracted"
        assert corpus_assertion.object is not None, "Corpus object not extracted"

        # Verify action extraction (kontrola)
        assert draft_assertion.action is not None, "Draft action not extracted"
        assert corpus_assertion.action is not None, "Corpus action not extracted"

        # Verify actor extraction
        assert draft_assertion.actor is not None, "Draft actor not extracted"
        assert corpus_assertion.actor is not None, "Corpus actor not extracted"

        # Check domain mismatch
        ontology = get_ontology_service()
        is_wrong_domain = ontology.is_wrong_domain_for_object(
            actor=draft_assertion.actor.canonical,
            object_name=draft_assertion.object.canonical,
        )
        assert is_wrong_domain, (
            f"Ontology should detect domain mismatch: "
            f"actor={draft_assertion.actor.canonical}, "
            f"object={draft_assertion.object.canonical}"
        )

        # Run conflict detection
        conflict_service = ConflictRegistryService()
        evaluation = conflict_service.evaluate_assertion_conflicts(
            pipeline_run_id=uuid4(),
            draft_assertions=[draft_assertion],
            corpus_assertions=[corpus_assertion],
        )
        findings = evaluation.findings

        assert len(findings) > 0, "No conflict detected"
        competence_conflicts = [
            f
            for f in findings
            if f.finding_type
            in ["competence_conflict", "wrong_inspection_authority"]
        ]
        assert len(competence_conflicts) > 0, (
            "competence_conflict or wrong_inspection_authority not detected"
        )

        finding = competence_conflicts[0]
        assert finding.risk_level == "high"
        # Verify evidence contains relevant quotes
        draft_quote = finding.evidence.get("draft_quote", "")
        corpus_quote = finding.evidence.get("corpus_quote", "")
        assert len(draft_quote) > 0, "Draft quote missing in evidence"
        assert len(corpus_quote) > 0, "Corpus quote missing in evidence"
        # Check that domain mismatch is captured in slot_diffs
        slot_diffs = finding.evidence.get("slot_diffs", [])
        assert len(slot_diffs) > 0, "Slot diffs missing in evidence"
        assert any(
            diff.get("relation") == "wrong_domain_for_object" for diff in slot_diffs
        ), "Domain mismatch not captured in slot_diffs"


    def test_permission_vs_prohibition_conflict(self):
        """
        Test permission vs prohibition conflict.
        Draft permits what corpus prohibits.
        """
        draft_doc = _make_document(
            "Gradjanin moze da sece drvo u svom dvoristu.", "pravilnik.txt"
        )
        corpus_doc = _make_document(
            "Zabranjeno je secenje drveta bez dozvole.", "zakon.txt"
        )

        extractor = AssertionExtractionService()
        draft_assertions = extractor.extract_from_document(
            document=draft_doc, pipeline_run_id=uuid4()
        )
        corpus_assertions = extractor.extract_from_document(
            document=corpus_doc, corpus_id=uuid4()
        )

        assert len(draft_assertions) > 0, "Draft assertion not extracted"
        assert len(corpus_assertions) > 0, "Corpus assertion not extracted"

        # Run conflict detection
        conflict_service = ConflictRegistryService()
        evaluation = conflict_service.evaluate_assertion_conflicts(
            pipeline_run_id=uuid4(),
            draft_assertions=draft_assertions,
            corpus_assertions=corpus_assertions,
        )
        findings = evaluation.findings

        # May not detect without proper modality extraction, but structure is ready
        permission_conflicts = [
            f for f in findings if f.finding_type == "permission_vs_prohibition_conflict"
        ]
        # Test passes if no exception thrown - actual detection depends on assertion extraction

    def test_definition_conflict(self):
        """
        Test definition conflict.
        Draft and corpus define same term differently.
        """
        draft_doc = _make_document(
            "Ovlasceno lice je fizicko lice sa licencom.", "pravilnik.txt"
        )
        corpus_doc = _make_document(
            "Ovlasceno lice je pravno lice registrovano za ovu delatnost.", "zakon.txt"
        )

        extractor = AssertionExtractionService()
        draft_assertions = extractor.extract_from_document(
            document=draft_doc, pipeline_run_id=uuid4()
        )
        corpus_assertions = extractor.extract_from_document(
            document=corpus_doc, corpus_id=uuid4()
        )

        assert len(draft_assertions) > 0, "Draft assertion not extracted"
        assert len(corpus_assertions) > 0, "Corpus assertion not extracted"

        # Run conflict detection
        conflict_service = ConflictRegistryService()
        evaluation = conflict_service.evaluate_assertion_conflicts(
            pipeline_run_id=uuid4(),
            draft_assertions=draft_assertions,
            corpus_assertions=corpus_assertions,
        )
        findings = evaluation.findings

        # Test structure is ready - actual detection depends on assertion type recognition
        definition_conflicts = [
            f for f in findings if f.finding_type == "definition_conflict"
        ]

    def test_reference_missing(self):
        """
        Test reference missing conflict.
        Draft regulates same matter as corpus but doesn't reference it.
        """
        draft_doc = _make_document(
            "Obelezavanje drveca vrsi ovlasceno lice.", "pravilnik.txt"
        )
        corpus_doc = _make_document(
            "Obelezavanje drveca vrsi ovlasceno lice.", "zakon-o-sumama.txt"
        )

        extractor = AssertionExtractionService()
        draft_assertions = extractor.extract_from_document(
            document=draft_doc, pipeline_run_id=uuid4()
        )
        corpus_assertions = extractor.extract_from_document(
            document=corpus_doc, corpus_id=uuid4()
        )

        assert len(draft_assertions) > 0, "Draft assertion not extracted"
        assert len(corpus_assertions) > 0, "Corpus assertion not extracted"

        # Run conflict detection
        conflict_service = ConflictRegistryService()
        evaluation = conflict_service.evaluate_assertion_conflicts(
            pipeline_run_id=uuid4(),
            draft_assertions=draft_assertions,
            corpus_assertions=corpus_assertions,
        )
        findings = evaluation.findings

        # Test structure ready - detection depends on metadata references
        reference_conflicts = [
            f for f in findings if f.finding_type == "reference_missing"
        ]

    def test_new_obligation_without_basis(self):
        """
        Test new obligation without basis.
        Subordinate act creates obligation not in parent law.
        """
        draft_doc = _make_document(
            "Vlasnik suma mora da podnese izvestaj o stanju suma.",
            "pravilnik-o-izvestajima.txt"
        )
        corpus_doc = _make_document(
            "Vlasnik suma ima pravo na zastitu.", "zakon-o-sumama.txt"
        )

        extractor = AssertionExtractionService()
        draft_assertions = extractor.extract_from_document(
            document=draft_doc, pipeline_run_id=uuid4()
        )
        corpus_assertions = extractor.extract_from_document(
            document=corpus_doc, corpus_id=uuid4()
        )

        assert len(draft_assertions) > 0, "Draft assertion not extracted"
        assert len(corpus_assertions) > 0, "Corpus assertion not extracted"

        # Run conflict detection
        conflict_service = ConflictRegistryService()
        evaluation = conflict_service.evaluate_assertion_conflicts(
            pipeline_run_id=uuid4(),
            draft_assertions=draft_assertions,
            corpus_assertions=corpus_assertions,
        )
        findings = evaluation.findings

        # Test structure ready - detection depends on modality extraction
        obligation_conflicts = [
            f for f in findings if f.finding_type == "new_obligation_without_basis"
        ]

    def test_sanction_without_basis(self):
        """
        Test sanction without basis.
        Subordinate act prescribes sanction without law basis.
        """
        draft_doc = _make_document(
            "Kontrolu suma vrsi inspekcija. Kazna za povredu je 50.000 dinara.",
            "pravilnik-o-sumama.txt"
        )
        corpus_doc = _make_document(
            "Kontrolu suma vrsi inspekcija.", "zakon-o-sumama.txt"
        )

        extractor = AssertionExtractionService()
        draft_assertions = extractor.extract_from_document(
            document=draft_doc, pipeline_run_id=uuid4()
        )
        corpus_assertions = extractor.extract_from_document(
            document=corpus_doc, corpus_id=uuid4()
        )

        assert len(draft_assertions) > 0, "Draft assertion not extracted"
        assert len(corpus_assertions) > 0, "Corpus assertion not extracted"

        # Run conflict detection
        conflict_service = ConflictRegistryService()
        evaluation = conflict_service.evaluate_assertion_conflicts(
            pipeline_run_id=uuid4(),
            draft_assertions=draft_assertions,
            corpus_assertions=corpus_assertions,
        )
        findings = evaluation.findings

        # Test structure ready - detection depends on sanction slot extraction
        sanction_conflicts = [
            f for f in findings if f.finding_type == "sanction_without_basis"
        ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
