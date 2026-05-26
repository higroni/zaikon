"""Rule-based draft review checkers."""

from calendar import monthrange
from functools import lru_cache
import re
from uuid import UUID

from zaikon.core.schemas import RiskLevel
from zaikon.modules.checkers.schemas import FindingRecord
from zaikon.modules.canonical.schemas import CanonicalDocument
from zaikon.modules.references.schemas import LegalReferenceRecord, ResolvedReferenceRecord

_DALJEM_TEKSTU_RE = re.compile(
    r"(?P<definition_text>[^.()]{3,160}?)\s*\(u\s+daljem\s+tekstu:\s*"
    r"(?P<term>[^)]+)\)",
    re.IGNORECASE,
)
_PLACEHOLDER_TERMS = {
    "nadlezni organ",
    "nadlezno ministarstvo",
    "drugi organ",
}
_SERBIAN_MONTHS = {
    "januar": 1,
    "februar": 2,
    "mart": 3,
    "april": 4,
    "maj": 5,
    "jun": 6,
    "jul": 7,
    "avgust": 8,
    "septembar": 9,
    "oktobar": 10,
    "novembar": 11,
    "decembar": 12,
}
_TEXTUAL_DATE_RE = re.compile(
    r"\b(?P<day>\d{1,2})\.\s*(?P<month>"
    + "|".join(_SERBIAN_MONTHS)
    + r")\s+(?P<year>\d{4})\b",
    re.IGNORECASE,
)


class ReferenceChecker:
    """Creates findings for references that cannot be resolved in the draft."""

    def check(
        self,
        *,
        pipeline_run_id: UUID,
        references: list[LegalReferenceRecord],
        resolved_references: list[ResolvedReferenceRecord],
    ) -> list[FindingRecord]:
        references_by_id = {
            reference.reference_id: reference for reference in references
        }
        findings: list[FindingRecord] = []

        for resolved in resolved_references:
            if resolved.resolution_status != "missing":
                continue
            reference = references_by_id.get(resolved.reference_id)
            if reference is None:
                continue

            findings.append(
                FindingRecord(
                    pipeline_run_id=pipeline_run_id,
                    finding_type="reference_missing",
                    risk_level=RiskLevel.high,
                    title="Reference target was not found",
                    explanation=(
                        "The draft contains an internal article reference that does "
                        "not resolve to an existing article or paragraph."
                    ),
                    recommendation=(
                        "Verify the cited article number and update the reference or "
                        "add the missing target provision."
                    ),
                    source_legal_unit_id=reference.source_legal_unit_id,
                    source_path=reference.source_path,
                    evidence={
                        "raw_text": reference.raw_text,
                        "target_article_number": reference.target_article_number,
                        "target_paragraph_number": reference.target_paragraph_number,
                        "resolution_note": resolved.resolution_note,
                    },
                )
            )

        return findings


class DefinitionConsistencyChecker:
    """Finds terms defined more than once with different wording."""

    def check(
        self,
        *,
        pipeline_run_id: UUID,
        document: CanonicalDocument,
    ) -> list[FindingRecord]:
        definitions_by_term: dict[str, list[dict]] = {}
        for unit in document.canonical_json.get("legal_units", []):
            content_text = unit.get("content_text") or ""
            for match in _DALJEM_TEKSTU_RE.finditer(content_text):
                term = match.group("term").strip(" :;,.")
                definition_text = match.group("definition_text").strip(" :;,.")
                normalized_term = self._normalize(term)
                definitions_by_term.setdefault(normalized_term, []).append(
                    {
                        "term": term,
                        "definition_text": definition_text,
                        "source_legal_unit_id": unit.get("legal_unit_id"),
                        "source_path": unit.get("path"),
                    }
                )

        findings: list[FindingRecord] = []
        for definitions in definitions_by_term.values():
            normalized_definitions = {
                self._normalize(definition["definition_text"])
                for definition in definitions
            }
            if len(definitions) < 2 or len(normalized_definitions) == 1:
                continue
            first = definitions[0]
            findings.append(
                FindingRecord(
                    pipeline_run_id=pipeline_run_id,
                    finding_type="definition_conflict",
                    risk_level=RiskLevel.medium,
                    title="Term is defined inconsistently",
                    explanation=(
                        "The same term appears to be defined more than once with "
                        "different wording in the draft."
                    ),
                    recommendation=(
                        "Keep one definition for the term or harmonize all repeated "
                        "definitions."
                    ),
                    source_legal_unit_id=first.get("source_legal_unit_id"),
                    source_path=first.get("source_path"),
                    evidence={
                        "term": first["term"],
                        "definitions": definitions,
                    },
                )
            )
        return findings

    def _normalize(self, value: str) -> str:
        return re.sub(r"\s+", " ", value.strip().lower())


class TerminologyConsistencyChecker:
    """Finds vague placeholder terms that should be resolved before review."""

    def check(
        self,
        *,
        pipeline_run_id: UUID,
        document: CanonicalDocument,
    ) -> list[FindingRecord]:
        findings: list[FindingRecord] = []
        for unit in document.canonical_json.get("legal_units", []):
            content_text = unit.get("content_text") or ""
            normalized = self._normalize(content_text)
            matched_terms = [
                term for term in _PLACEHOLDER_TERMS if term in normalized
            ]
            if not matched_terms:
                continue
            findings.append(
                FindingRecord(
                    pipeline_run_id=pipeline_run_id,
                    finding_type="terminology_inconsistent",
                    risk_level=RiskLevel.low,
                    title="Vague institutional term should be defined",
                    explanation=(
                        "The draft uses a broad institutional term that may be "
                        "ambiguous without a definition or a precise authority."
                    ),
                    recommendation=(
                        "Define the term or replace it with the exact institution "
                        "responsible for the obligation."
                    ),
                    source_legal_unit_id=unit.get("legal_unit_id"),
                    source_path=unit.get("path"),
                    evidence={"matched_terms": matched_terms},
                )
            )
        return findings

    def _normalize(self, value: str) -> str:
        return re.sub(r"\s+", " ", value.strip().lower())


class TemporalValidityChecker:
    """Finds impossible textual dates in Serbian legal provisions."""

    def check(
        self,
        *,
        pipeline_run_id: UUID,
        document: CanonicalDocument,
    ) -> list[FindingRecord]:
        findings: list[FindingRecord] = []
        for unit in document.canonical_json.get("legal_units", []):
            content_text = unit.get("content_text") or ""
            invalid_dates = []
            for match in _TEXTUAL_DATE_RE.finditer(content_text):
                day = int(match.group("day"))
                month = _SERBIAN_MONTHS[match.group("month").lower()]
                year = int(match.group("year"))
                if day > monthrange(year, month)[1]:
                    invalid_dates.append(match.group(0))
            if not invalid_dates:
                continue
            findings.append(
                FindingRecord(
                    pipeline_run_id=pipeline_run_id,
                    finding_type="temporal_validity_issue",
                    risk_level=RiskLevel.medium,
                    title="Invalid effective date",
                    explanation=(
                        "The draft contains a calendar date that does not exist, "
                        "which can make the temporal rule unenforceable."
                    ),
                    recommendation="Correct the date before publishing the draft.",
                    source_legal_unit_id=unit.get("legal_unit_id"),
                    source_path=unit.get("path"),
                    evidence={"invalid_dates": invalid_dates},
                )
            )
        return findings


@lru_cache
def get_reference_checker() -> ReferenceChecker:
    return ReferenceChecker()


@lru_cache
def get_definition_consistency_checker() -> DefinitionConsistencyChecker:
    return DefinitionConsistencyChecker()


@lru_cache
def get_terminology_consistency_checker() -> TerminologyConsistencyChecker:
    return TerminologyConsistencyChecker()


@lru_cache
def get_temporal_validity_checker() -> TemporalValidityChecker:
    return TemporalValidityChecker()
