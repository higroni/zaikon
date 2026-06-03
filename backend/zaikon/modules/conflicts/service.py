"""Registry for conflict types supported by the rule engine."""

from functools import lru_cache
import json
from pathlib import Path
from uuid import UUID, uuid5, NAMESPACE_URL
import difflib

from zaikon.core.config import settings
from zaikon.core.schemas import RiskLevel
from zaikon.modules.assertions.schemas import NormativeAssertion
from zaikon.modules.checkers.schemas import FindingRecord
from zaikon.modules.conflicts.schemas import AssertionConflictEvaluation
from zaikon.modules.conflicts.schemas import ConflictCandidate
from zaikon.modules.conflicts.schemas import ConflictTypeRecord
from zaikon.modules.ontology.service import get_ontology_service


_CATEGORY_TYPES: dict[str, list[str]] = {
    "hierarchy_and_legal_basis": [
        "source_hierarchy_conflict",
        "ultra_vires_conflict",
        "delegation_missing",
        "delegation_exceeded",
        "reserved_matter_conflict",
        "lex_specialis_conflict",
        "lex_posterior_conflict",
        "constitutional_alignment_risk",
    ],
    "competence_and_institutions": [
        "competence_conflict",
        "wrong_inspection_authority",
        "missing_competent_authority",
        "overlapping_competence_conflict",
        "competence_transfer_conflict",
        "local_vs_republic_competence_conflict",
        "independent_body_competence_conflict",
        "appeal_authority_conflict",
    ],
    "actors_and_personal_scope": [
        "authority_scope_conflict",
        "obligation_bearer_changed",
        "right_holder_changed",
        "personal_scope_expanded",
        "personal_scope_narrowed",
        "protected_category_conflict",
        "representative_authority_conflict",
    ],
    "modality_rights_obligations": [
        "permission_vs_prohibition_conflict",
        "obligation_vs_discretion_conflict",
        "discretion_vs_obligation_conflict",
        "right_removed_conflict",
        "prohibition_removed_conflict",
        "new_obligation_without_basis",
        "conflicting_obligations",
        "impossible_obligation",
    ],
    "material_scope": [
        "action_scope_mismatch",
        "object_scope_expanded",
        "object_scope_narrowed",
        "territorial_scope_conflict",
        "domain_mismatch_conflict",
        "threshold_mismatch",
        "category_classification_conflict",
    ],
    "deadlines_time_validity": [
        "deadline_mismatch",
        "deadline_start_event_mismatch",
        "deadline_end_event_mismatch",
        "calendar_type_mismatch",
        "deadline_missing",
        "deadline_added_without_basis",
        "retroactivity_conflict",
        "effective_date_conflict",
        "validity_period_conflict",
        "transitional_period_conflict",
    ],
    "conditions_exceptions": [
        "condition_added_conflict",
        "condition_removed_conflict",
        "condition_mismatch",
        "exception_added_conflict",
        "exception_removed_conflict",
        "cumulative_vs_alternative_conflict",
        "threshold_condition_conflict",
    ],
    "definitions_terminology": [
        "definition_conflict",
        "undefined_term",
        "reserved_term_misuse",
        "terminology_inconsistent",
        "translation_alignment_conflict",
        "classification_definition_conflict",
        "abbreviation_conflict",
    ],
    "references": [
        "reference_missing",
        "reference_stale",
        "reference_ambiguous",
        "reference_wrong_target",
        "reference_scope_mismatch",
        "circular_reference",
        "external_reference_unavailable",
        "official_gazette_reference_mismatch",
    ],
    "finance_budget": [
        "budget_impact_missing",
        "fee_without_legal_basis",
        "fee_amount_mismatch",
        "funding_source_missing",
        "state_aid_risk",
        "budget_classification_conflict",
    ],
    "sanctions_enforcement": [
        "sanction_without_basis",
        "sanction_amount_mismatch",
        "sanction_type_mismatch",
        "double_sanction_risk",
        "missing_enforcement_measure",
        "disproportionate_sanction_risk",
        "inspection_measure_conflict",
    ],
    "procedure_rights_remedies": [
        "appeal_right_missing",
        "appeal_deadline_mismatch",
        "due_process_risk",
        "burden_of_proof_conflict",
        "silence_of_administration_conflict",
        "service_delivery_conflict",
        "administrative_fee_conflict",
    ],
    "data_registers_transparency": [
        "personal_data_basis_missing",
        "data_minimization_risk",
        "confidentiality_vs_publication_conflict",
        "registry_competence_conflict",
        "retention_period_conflict",
        "access_to_information_conflict",
    ],
    "eu_alignment": [
        "eu_alignment_statement_missing",
        "eu_alignment_table_missing",
        "eu_celex_missing",
        "eu_row_unmapped",
        "domestic_article_uncovered_by_alignment",
        "partial_alignment_without_reason",
        "non_alignment_without_plan",
        "not_transposable_without_reason",
        "eu_term_translation_conflict",
        "eu_effective_sanction_missing",
        "gold_plating_risk",
        "alignment_stale_after_draft_change",
    ],
    "procedural_compliance": [
        "ria_missing",
        "ria_incomplete",
        "public_consultation_missing",
        "public_consultation_duration_short",
        "public_consultation_report_missing",
        "official_opinion_missing",
        "negative_opinion_unresolved",
        "conditional_opinion_unresolved",
        "fiscal_assessment_missing",
        "committee_gate_not_ready",
        "parliamentary_material_incomplete",
    ],
    "internal_consistency": [
        "internal_norm_conflict",
        "internal_duplicate_provision",
        "internal_definition_conflict",
        "numbering_structure_error",
        "transitional_final_clause_missing",
        "repeal_clause_conflict",
        "effective_clause_missing",
        "drafting_style_warning",
    ],
}

_HIGH_SEVERITY_TYPES = {
    "source_hierarchy_conflict",
    "ultra_vires_conflict",
    "reserved_matter_conflict",
    "competence_conflict",
    "wrong_inspection_authority",
    "authority_scope_conflict",
    "permission_vs_prohibition_conflict",
    "right_removed_conflict",
    "new_obligation_without_basis",
    "deadline_mismatch",
    "reference_stale",
    "fee_without_legal_basis",
    "sanction_without_basis",
    "appeal_right_missing",
    "personal_data_basis_missing",
    "eu_alignment_table_missing",
    "negative_opinion_unresolved",
}

_ACTIVE_WARNING_TYPES = {
    "authority_scope_conflict",
    "deadline_mismatch",
    "competence_conflict",
    "modality_conflict",
    "reference_missing",
    "reference_stale",
    "definition_conflict",
    "terminology_inconsistent",
    "drafting_style_warning",
}


class ConflictRegistryService:
    """Exposes the complete conflict taxonomy as engine registry records."""

    def __init__(self, rules_dir: Path | None = None) -> None:
        self.rules_dir = rules_dir or (
            settings.base_dir / "backend" / "zaikon" / "rules" / "conflicts"
        )
        self._registry = self._load_registry()
        self._active_rules = self._load_active_rules()

    def reload(self) -> None:
        self._registry = self._load_registry()
        self._active_rules = self._load_active_rules()

    def list_conflict_types(
        self, *, category: str | None = None
    ) -> list[ConflictTypeRecord]:
        records = [
            self._record(finding_type=finding_type, category=category_name)
            for category_name, category_record in self._categories().items()
            for finding_type in category_record.get("finding_types", [])
        ]
        if category is not None:
            records = [record for record in records if record.category == category]
        return records

    def get_conflict_type(self, finding_type: str) -> ConflictTypeRecord | None:
        for record in self.list_conflict_types():
            if record.finding_type == finding_type:
                return record
        return None

    def list_categories(self) -> list[str]:
        return sorted(self._categories())

    def evaluate_assertion_conflicts(
        self,
        *,
        pipeline_run_id: UUID,
        draft_assertions: list[NormativeAssertion],
        corpus_assertions: list[NormativeAssertion],
    ) -> AssertionConflictEvaluation:
        candidates: list[ConflictCandidate] = []
        findings: list[FindingRecord] = []

        for draft in draft_assertions:
            for corpus in corpus_assertions:
                candidate = self._candidate(draft, corpus)
                if candidate is None:
                    continue
                candidates.append(candidate)
                findings.extend(
                    self._evaluate_candidate(
                        pipeline_run_id=pipeline_run_id,
                        draft=draft,
                        corpus=corpus,
                        candidate=candidate,
                    )
                )

        return AssertionConflictEvaluation(
            candidates=candidates,
            findings=self._deduplicate_findings(findings),
            trace={
                "draft_assertion_count": len(draft_assertions),
                "corpus_assertion_count": len(corpus_assertions),
                "candidate_count": len(candidates),
                "finding_count": len(findings),
                "engine_scope": "registered_taxonomy_with_slot_based_active_rules",
            },
        )

    def _record(self, *, finding_type: str, category: str) -> ConflictTypeRecord:
        high_severity_types = set(self._registry.get("high_severity_types", []))
        active_warning_types = set(self._registry.get("active_warning_types", []))
        return ConflictTypeRecord(
            finding_type=finding_type,
            category=category,
            default_severity="high"
            if finding_type in high_severity_types
            else "medium",
            engine_status="active_warning"
            if finding_type in active_warning_types
            else "needs_expert_review",
            required_slots=self._required_slots(category),
            evidence_required=list(
                self._registry.get(
                    "default_evidence_required",
                    ["draft_quote", "corpus_quote", "slot_diffs"],
                )
            ),
            description=finding_type.replace("_", " "),
        )

    def _categories(self) -> dict:
        categories = self._registry.get("categories", {})
        return categories if isinstance(categories, dict) else {}

    def _required_slots(self, category: str) -> list[str]:
        category_record = self._categories().get(category, {})
        return list(category_record.get("required_slots", []))

    def _load_registry(self) -> dict:
        path = self.rules_dir / "registry.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self._validate_registry(payload)
        return payload

    def _validate_registry(self, payload: dict) -> None:
        categories = payload.get("categories")
        if not isinstance(categories, dict) or not categories:
            raise ValueError("Conflict registry must define categories")
        finding_types = []
        for category, record in categories.items():
            if not isinstance(record.get("finding_types"), list):
                raise ValueError(f"Conflict category missing finding_types: {category}")
            finding_types.extend(record["finding_types"])
        duplicates = {
            finding_type
            for finding_type in finding_types
            if finding_types.count(finding_type) > 1
        }
        if duplicates:
            raise ValueError(
                "Conflict registry contains duplicate finding types: "
                + ", ".join(sorted(duplicates))
            )
        finding_type_set = set(finding_types)
        for list_name in ("high_severity_types", "active_warning_types"):
            unknown = set(payload.get(list_name, [])) - finding_type_set
            if unknown:
                raise ValueError(
                    f"Conflict registry {list_name} contains unknown finding types: "
                    + ", ".join(sorted(unknown))
                )

    def _candidate(
        self, draft: NormativeAssertion, corpus: NormativeAssertion
    ) -> ConflictCandidate | None:
        match_reasons = []
        base_score = 0.0
        
        # Exact matches (high confidence)
        if self._same_slot(draft.action, corpus.action):
            match_reasons.append("same_action")
            base_score += 0.30
        elif self._similar_slot(draft.action, corpus.action, threshold=0.7):
            match_reasons.append("similar_action")
            base_score += 0.20
            
        if self._same_slot(draft.object, corpus.object):
            match_reasons.append("same_object")
            base_score += 0.30
        elif self._similar_slot(draft.object, corpus.object, threshold=0.7):
            match_reasons.append("similar_object")
            base_score += 0.20
            
        if self._same_slot(draft.domain, corpus.domain):
            match_reasons.append("same_domain")
            base_score += 0.15
            
        if draft.deadline is not None and corpus.deadline is not None:
            match_reasons.append("both_have_deadline")
            base_score += 0.10
            
        # Semantic similarity on source quotes (fallback)
        if base_score < 0.3:
            quote_similarity = self._text_similarity(draft.source_quote, corpus.source_quote)
            if quote_similarity > 0.6:
                match_reasons.append("similar_quote")
                base_score += quote_similarity * 0.25
        
        # Minimum threshold
        if base_score < 0.25:
            return None
            
        # Must have at least action or deadline match
        has_action = "same_action" in match_reasons or "similar_action" in match_reasons
        has_deadline = "both_have_deadline" in match_reasons
        if not (has_action or has_deadline):
            return None
            
        score = min(0.95, base_score)
        return ConflictCandidate(
            candidate_id=str(
                uuid5(
                    NAMESPACE_URL,
                    f"{draft.assertion_id}:{corpus.assertion_id}:{','.join(match_reasons)}",
                )
            ),
            draft_assertion_id=str(draft.assertion_id),
            corpus_assertion_id=str(corpus.assertion_id),
            score=score,
            match_reasons=match_reasons,
        )

    def _evaluate_candidate(
        self,
        *,
        pipeline_run_id: UUID,
        draft: NormativeAssertion,
        corpus: NormativeAssertion,
        candidate: ConflictCandidate,
    ) -> list[FindingRecord]:
        findings = []
        if self._deadline_mismatch(draft, corpus):
            rule = self._rule("deadline_mismatch")
            findings.append(
                self._finding(
                    pipeline_run_id=pipeline_run_id,
                    finding_type="deadline_mismatch",
                    risk_level=self._rule_risk(rule),
                    title=rule["title"],
                    explanation=rule["explanation"],
                    recommendation=rule["recommendation"],
                    rule_id=rule["rule_id"],
                    draft=draft,
                    corpus=corpus,
                    candidate=candidate,
                    slot_diffs=[
                        {
                            "slot": "deadline",
                            "draft_value": self._deadline_value(draft),
                            "corpus_value": self._deadline_value(corpus),
                            "relation": "not_equal",
                        }
                    ],
                )
            )
        if self._authority_scope_conflict(draft, corpus):
            rule = self._rule("authority_scope_conflict")
            findings.append(
                self._finding(
                    pipeline_run_id=pipeline_run_id,
                    finding_type="authority_scope_conflict",
                    risk_level=self._rule_risk(rule),
                    title=rule["title"],
                    explanation=rule["explanation"],
                    recommendation=rule["recommendation"],
                    rule_id=rule["rule_id"],
                    draft=draft,
                    corpus=corpus,
                    candidate=candidate,
                    slot_diffs=[
                        {
                            "slot": "actor",
                            "draft_value": self._slot_value(draft.actor),
                            "corpus_value": self._slot_value(corpus.actor),
                            "relation": "broader_than_allowed",
                        }
                    ],
                )
            )
        if self._competence_conflict(draft, corpus):
            rule = self._rule("competence_conflict")
            findings.append(
                self._finding(
                    pipeline_run_id=pipeline_run_id,
                    finding_type="competence_conflict",
                    risk_level=self._rule_risk(rule),
                    title=rule["title"],
                    explanation=rule["explanation"],
                    recommendation=rule["recommendation"],
                    rule_id=rule["rule_id"],
                    draft=draft,
                    corpus=corpus,
                    candidate=candidate,
                    slot_diffs=[
                        {
                            "slot": "actor_domain",
                            "draft_value": self._slot_value(draft.actor),
                            "corpus_value": self._slot_value(corpus.actor),
                            "relation": "wrong_domain_for_object",
                        }
                    ],
                )
            )
        if self._permission_vs_prohibition_conflict(draft, corpus):
            rule = self._rule("permission_vs_prohibition_conflict")
            findings.append(
                self._finding(
                    pipeline_run_id=pipeline_run_id,
                    finding_type="permission_vs_prohibition_conflict",
                    risk_level=self._rule_risk(rule),
                    title=rule["title"],
                    explanation=rule["explanation"],
                    recommendation=rule["recommendation"],
                    rule_id=rule["rule_id"],
                    draft=draft,
                    corpus=corpus,
                    candidate=candidate,
                    slot_diffs=[
                        {
                            "slot": "modality",
                            "draft_value": draft.modality,
                            "corpus_value": corpus.modality,
                            "relation": "opposes",
                        }
                    ],
                )
            )
        if self._definition_conflict(draft, corpus):
            rule = self._rule("definition_conflict")
            findings.append(
                self._finding(
                    pipeline_run_id=pipeline_run_id,
                    finding_type="definition_conflict",
                    risk_level=self._rule_risk(rule),
                    title=rule["title"],
                    explanation=rule["explanation"],
                    recommendation=rule["recommendation"],
                    rule_id=rule["rule_id"],
                    draft=draft,
                    corpus=corpus,
                    candidate=candidate,
                    slot_diffs=[
                        {
                            "slot": "object",
                            "draft_value": self._slot_value(draft.object),
                            "corpus_value": self._slot_value(corpus.object),
                            "relation": "definition_differs",
                        }
                    ],
                )
            )
        if self._reference_missing(draft, corpus):
            rule = self._rule("reference_missing")
            findings.append(
                self._finding(
                    pipeline_run_id=pipeline_run_id,
                    finding_type="reference_missing",
                    risk_level=self._rule_risk(rule),
                    title=rule["title"],
                    explanation=rule["explanation"],
                    recommendation=rule["recommendation"],
                    rule_id=rule["rule_id"],
                    draft=draft,
                    corpus=corpus,
                    candidate=candidate,
                    slot_diffs=[
                        {
                            "slot": "reference",
                            "draft_value": "missing",
                            "corpus_value": corpus.source_path,
                            "relation": "no_reference",
                        }
                    ],
                )
            )
        if self._new_obligation_without_basis(draft, corpus):
            rule = self._rule("new_obligation_without_basis")
            findings.append(
                self._finding(
                    pipeline_run_id=pipeline_run_id,
                    finding_type="new_obligation_without_basis",
                    risk_level=self._rule_risk(rule),
                    title=rule["title"],
                    explanation=rule["explanation"],
                    recommendation=rule["recommendation"],
                    rule_id=rule["rule_id"],
                    draft=draft,
                    corpus=corpus,
                    candidate=candidate,
                    slot_diffs=[
                        {
                            "slot": "modality",
                            "draft_value": draft.modality,
                            "corpus_value": "not_in_law",
                            "relation": "new_obligation",
                        }
                    ],
                )
            )
        if self._sanction_without_basis(draft, corpus):
            rule = self._rule("sanction_without_basis")
            findings.append(
                self._finding(
                    pipeline_run_id=pipeline_run_id,
                    finding_type="sanction_without_basis",
                    risk_level=self._rule_risk(rule),
                    title=rule["title"],
                    explanation=rule["explanation"],
                    recommendation=rule["recommendation"],
                    rule_id=rule["rule_id"],
                    draft=draft,
                    corpus=corpus,
                    candidate=candidate,
                    slot_diffs=[
                        {
                            "slot": "sanction",
                            "draft_value": self._slot_value(draft.sanction),
                            "corpus_value": "not_in_law",
                            "relation": "contains_sanction",
                        }
                    ],
                )
            )
        return findings

    def _deadline_mismatch(
        self, draft: NormativeAssertion, corpus: NormativeAssertion
    ) -> bool:
        return (
            draft.deadline is not None
            and corpus.deadline is not None
            and self._same_slot(draft.action, corpus.action)
            and (
                draft.deadline.value != corpus.deadline.value
                or draft.deadline.unit != corpus.deadline.unit
            )
        )

    def _authority_scope_conflict(
        self, draft: NormativeAssertion, corpus: NormativeAssertion
    ) -> bool:
        if not (self._same_slot(draft.action, corpus.action) and self._same_slot(draft.object, corpus.object)):
            return False
        ontology = get_ontology_service()
        return ontology.is_broader_actor(
            draft.actor.canonical if draft.actor else None,
            corpus.actor.canonical if corpus.actor else None,
        )

    def _competence_conflict(
        self, draft: NormativeAssertion, corpus: NormativeAssertion
    ) -> bool:
        if draft.assertion_type != "competence" and corpus.assertion_type != "competence":
            return False
        if not (self._same_slot(draft.action, corpus.action) and self._same_slot(draft.object, corpus.object)):
            return False
        ontology = get_ontology_service()
        draft_actor = draft.actor.canonical if draft.actor else None
        corpus_actor = corpus.actor.canonical if corpus.actor else None
        object_name = draft.object.canonical if draft.object else None
        return (
            draft_actor != corpus_actor
            and ontology.is_wrong_domain_for_object(
                actor=draft_actor,
                object_name=object_name,
            )
            and not ontology.is_wrong_domain_for_object(
                actor=corpus_actor,
                object_name=object_name,
            )
        )
    def _permission_vs_prohibition_conflict(
        self, draft: NormativeAssertion, corpus: NormativeAssertion
    ) -> bool:
        """Check if draft permits what corpus prohibits or vice versa."""
        if not (self._same_slot(draft.action, corpus.action) and self._same_slot(draft.object, corpus.object)):
            return False
        if draft.modality is None or corpus.modality is None:
            return False
        # Permission vs prohibition
        permission_modalities = {"may", "can", "is_permitted", "has_right"}
        prohibition_modalities = {"must_not", "cannot", "is_prohibited", "is_forbidden"}
        draft_permits = draft.modality.lower() in permission_modalities
        draft_prohibits = draft.modality.lower() in prohibition_modalities
        corpus_permits = corpus.modality.lower() in permission_modalities
        corpus_prohibits = corpus.modality.lower() in prohibition_modalities
        return (draft_permits and corpus_prohibits) or (draft_prohibits and corpus_permits)

    def _definition_conflict(
        self, draft: NormativeAssertion, corpus: NormativeAssertion
    ) -> bool:
        """Check if draft and corpus define the same term differently."""
        if draft.assertion_type != "definition" or corpus.assertion_type != "definition":
            return False
        if not self._same_slot(draft.object, corpus.object):
            return False
        # If they define the same term but have different source quotes, it's a conflict
        return draft.source_quote != corpus.source_quote

    def _reference_missing(
        self, draft: NormativeAssertion, corpus: NormativeAssertion
    ) -> bool:
        """Check if draft regulates same matter as corpus but doesn't reference it."""
        if not (self._same_slot(draft.action, corpus.action) and self._same_slot(draft.object, corpus.object)):
            return False
        # Check if draft metadata contains any reference to corpus
        draft_refs = draft.metadata.get("references", [])
        corpus_path = corpus.source_path
        corpus_filename = corpus.filename
        # If draft doesn't reference the corpus document, it's missing
        for ref in draft_refs:
            if corpus_path in str(ref) or corpus_filename in str(ref):
                return False
        return True

    def _new_obligation_without_basis(
        self, draft: NormativeAssertion, corpus: NormativeAssertion
    ) -> bool:
        """Check if subordinate act creates new obligation not in parent law."""
        # Check if draft is from subordinate act (pravilnik, uredba, etc.)
        draft_filename = draft.filename.lower()
        is_subordinate = any(
            keyword in draft_filename
            for keyword in ["pravilnik", "uredba", "naredba", "uputstvo"]
        )
        if not is_subordinate:
            return False
        # Check if corpus is from law (zakon)
        corpus_filename = corpus.filename.lower()
        is_law = "zakon" in corpus_filename
        if not is_law:
            return False
        # Check if draft creates obligation (must, shall)
        if draft.modality is None:
            return False
        obligation_modalities = {"must", "shall", "is_required", "is_obliged"}
        draft_creates_obligation = draft.modality.lower() in obligation_modalities
        if not draft_creates_obligation:
            return False
        # Check if same obligation exists in law
        if self._same_slot(draft.action, corpus.action) and self._same_slot(draft.object, corpus.object):
            corpus_has_obligation = (
                corpus.modality is not None
                and corpus.modality.lower() in obligation_modalities
            )
            if corpus_has_obligation:
                return False
        # New obligation in subordinate act without basis in law
        return True

    def _sanction_without_basis(
        self, draft: NormativeAssertion, corpus: NormativeAssertion
    ) -> bool:
        """Check if subordinate act prescribes sanction without law basis."""
        # Check if draft is from subordinate act
        draft_filename = draft.filename.lower()
        is_subordinate = any(
            keyword in draft_filename
            for keyword in ["pravilnik", "uredba", "naredba", "uputstvo"]
        )
        if not is_subordinate:
            return False
        # Check if draft contains sanction
        if draft.sanction is None:
            return False
        # Check if corpus is from law
        corpus_filename = corpus.filename.lower()
        is_law = "zakon" in corpus_filename
        if not is_law:
            return False
        # Check if law provides basis for this sanction
        if self._same_slot(draft.action, corpus.action) and corpus.sanction is not None:
            return False
        # Sanction in subordinate act without basis in law
        return True


    def _finding(
        self,
        *,
        pipeline_run_id: UUID,
        finding_type: str,
        risk_level: RiskLevel,
        title: str,
        explanation: str,
        recommendation: str,
        rule_id: str,
        draft: NormativeAssertion,
        corpus: NormativeAssertion,
        candidate: ConflictCandidate,
        slot_diffs: list[dict],
    ) -> FindingRecord:
        return FindingRecord(
            pipeline_run_id=pipeline_run_id,
            finding_type=finding_type,
            risk_level=risk_level,
            title=title,
            explanation=explanation,
            recommendation=recommendation,
            source_legal_unit_id=draft.legal_unit_id,
            source_path=draft.source_path,
            evidence={
                "draft_assertion_id": str(draft.assertion_id),
                "corpus_assertion_id": str(corpus.assertion_id),
                "draft_quote": draft.source_quote,
                "corpus_quote": corpus.source_quote,
                "draft_path": draft.source_path,
                "corpus_path": corpus.source_path,
                "draft_filename": draft.filename,
                "corpus_filename": corpus.filename,
                "slot_diffs": slot_diffs,
                "rule_id": rule_id,
                "rule_version": "0.1.0",
                "candidate": candidate.model_dump(mode="json"),
            },
        )

    def _deduplicate_findings(self, findings: list[FindingRecord]) -> list[FindingRecord]:
        seen = set()
        unique = []
        for finding in findings:
            evidence = finding.evidence
            key = (
                finding.finding_type,
                evidence.get("draft_assertion_id"),
                evidence.get("corpus_assertion_id"),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(finding)
        return unique

    def _same_slot(self, draft_slot, corpus_slot) -> bool:
        return (
            draft_slot is not None
            and corpus_slot is not None
            and draft_slot.canonical == corpus_slot.canonical
        )
    def _similar_slot(self, draft_slot, corpus_slot, threshold: float = 0.7) -> bool:
        """Check if two slots are semantically similar using string similarity."""
        if draft_slot is None or corpus_slot is None:
            return False
        if draft_slot.canonical == corpus_slot.canonical:
            return True
        similarity = self._text_similarity(draft_slot.canonical, corpus_slot.canonical)
        return similarity >= threshold
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using SequenceMatcher (0.0 to 1.0)."""
        if not text1 or not text2:
            return 0.0
        # Normalize texts
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()
        if t1 == t2:
            return 1.0
        # Use difflib's SequenceMatcher for similarity
        return difflib.SequenceMatcher(None, t1, t2).ratio()


    def _slot_value(self, slot) -> str | None:
        return slot.canonical if slot is not None else None

    def _deadline_value(self, assertion: NormativeAssertion) -> str | None:
        if assertion.deadline is None:
            return None
        return f"{assertion.deadline.value} {assertion.deadline.unit}"

    def _load_active_rules(self) -> dict:
        path = self.rules_dir / "active_rules.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self._validate_active_rules(payload)
        return payload

    def _validate_active_rules(self, payload: dict) -> None:
        rules = payload.get("rules")
        if not isinstance(rules, list) or not rules:
            raise ValueError("Active conflict rules must define a non-empty rules list")
        registry_types = {record.finding_type for record in self.list_conflict_types()}
        for rule in rules:
            finding_type = rule.get("finding_type")
            if finding_type not in registry_types:
                raise ValueError(f"Active rule uses unregistered finding_type: {finding_type}")
            for key in ("rule_id", "title", "explanation", "recommendation"):
                if not rule.get(key):
                    raise ValueError(f"Active rule missing {key}: {finding_type}")

    def _rule(self, finding_type: str) -> dict:
        for rule in self._active_rules.get("rules", []):
            if rule.get("finding_type") == finding_type:
                return rule
        raise KeyError(f"Active conflict rule not found: {finding_type}")

    def _rule_risk(self, rule: dict) -> RiskLevel:
        return RiskLevel(rule.get("risk_level", "medium"))


def _required_slots(category: str) -> list[str]:
    mapping = {
        "hierarchy_and_legal_basis": ["source_rank", "document_type", "legal_basis"],
        "competence_and_institutions": ["actor", "competence", "action", "object"],
        "actors_and_personal_scope": ["actor", "action", "object"],
        "modality_rights_obligations": ["modality", "action", "object"],
        "material_scope": ["action", "object", "material_scope"],
        "deadlines_time_validity": ["deadline", "deadline_start_event"],
        "conditions_exceptions": ["condition", "exception", "action"],
        "definitions_terminology": ["term", "definition"],
        "references": ["reference_target"],
        "finance_budget": ["amount", "budget_impact", "legal_basis"],
        "sanctions_enforcement": ["sanction", "action", "legal_basis"],
        "procedure_rights_remedies": ["procedure_stage", "right", "remedy"],
        "data_registers_transparency": ["data_fields", "purpose", "legal_basis"],
        "eu_alignment": ["eu_source", "alignment_status"],
        "procedural_compliance": ["procedure_stage", "required_artifact"],
        "internal_consistency": ["source_quote", "source_path"],
    }
    return mapping.get(category, [])


@lru_cache
def get_conflict_registry_service() -> ConflictRegistryService:
    return ConflictRegistryService()
