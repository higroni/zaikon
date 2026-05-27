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
_OBLIGATION_RE = re.compile(r"\b(?:mora|duzan|duzna|duzno|obavezan|obavezna)\b")
_PROHIBITION_RE = re.compile(r"\b(?:ne\s+sme|zabranjuje\s+se|zabranjeno)\b")
_REPEAL_RE = re.compile(r"\b(?:prestaje\s+da\s+vazi|prestaju\s+da\s+vaze)\b")
_FOLD_MAP = str.maketrans(
    {
        "č": "c",
        "ć": "c",
        "š": "s",
        "đ": "dj",
        "ž": "z",
        "Č": "c",
        "Ć": "c",
        "Š": "s",
        "Đ": "dj",
        "Ž": "z",
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "ђ": "dj",
        "е": "e",
        "ж": "z",
        "з": "z",
        "и": "i",
        "ј": "j",
        "к": "k",
        "л": "l",
        "љ": "lj",
        "м": "m",
        "н": "n",
        "њ": "nj",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "ћ": "c",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "c",
        "ч": "c",
        "џ": "dz",
        "ш": "s",
        "А": "a",
        "Б": "b",
        "В": "v",
        "Г": "g",
        "Д": "d",
        "Ђ": "dj",
        "Е": "e",
        "Ж": "z",
        "З": "z",
        "И": "i",
        "Ј": "j",
        "К": "k",
        "Л": "l",
        "Љ": "lj",
        "М": "m",
        "Н": "n",
        "Њ": "nj",
        "О": "o",
        "П": "p",
        "Р": "r",
        "С": "s",
        "Т": "t",
        "Ћ": "c",
        "У": "u",
        "Ф": "f",
        "Х": "h",
        "Ц": "c",
        "Ч": "c",
        "Џ": "dz",
        "Ш": "s",
    }
)
_TREE_MARKING_RE = re.compile(r"\bobelezavanj\w*\s+(?:drveca|stabala|sumsk\w+\s+stabala)\b")
_BROAD_ACTOR_RE = re.compile(
    r"\b(?:svaki\s+gradjanin|svako\s+lice|bilo\s+koje\s+lice|fizicko\s+lice|gradjanin)\b"
)
_AUTHORIZED_ACTOR_RE = re.compile(
    r"\b(?:ovlascen\w+\s+(?:preduzec\w+|pravnom?\s+lic\w+|lic\w+)|strucn\w+\s+sluzb\w+)\b"
)


def _normalize_legal_text(value: str) -> str:
    folded = value.translate(_FOLD_MAP).lower()
    return re.sub(r"\s+", " ", folded)


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


class NormConflictChecker:
    """Flags provisions that combine obligation and prohibition signals."""

    def check(
        self,
        *,
        pipeline_run_id: UUID,
        document: CanonicalDocument,
    ) -> list[FindingRecord]:
        findings: list[FindingRecord] = []
        for unit in document.canonical_json.get("legal_units", []):
            content_text = unit.get("content_text") or ""
            normalized = content_text.lower()
            if not (_OBLIGATION_RE.search(normalized) and _PROHIBITION_RE.search(normalized)):
                continue
            findings.append(
                FindingRecord(
                    pipeline_run_id=pipeline_run_id,
                    finding_type="possible_norm_conflict",
                    risk_level=RiskLevel.medium,
                    title="Possible conflict between obligation and prohibition",
                    explanation=(
                        "The same provision appears to combine mandatory and "
                        "prohibitive language, which may require legal review."
                    ),
                    recommendation=(
                        "Separate the obligation and prohibition or clarify the "
                        "conditions under which each rule applies."
                    ),
                    source_legal_unit_id=unit.get("legal_unit_id"),
                    source_path=unit.get("path"),
                    evidence={"content_text": content_text},
                )
            )
        return findings


class CorpusAuthorityConflictChecker:
    """Flags draft permissions that conflict with authorized-actor rules in corpus."""

    def check(
        self,
        *,
        pipeline_run_id: UUID,
        document: CanonicalDocument,
        corpus_documents: list[CanonicalDocument],
    ) -> list[FindingRecord]:
        findings: list[FindingRecord] = []
        corpus_units = self._authorized_tree_marking_units(corpus_documents)
        if not corpus_units:
            return findings

        for unit in document.canonical_json.get("legal_units", []):
            content_text = unit.get("content_text") or ""
            normalized = _normalize_legal_text(content_text)
            if not (
                _TREE_MARKING_RE.search(normalized)
                and _BROAD_ACTOR_RE.search(normalized)
            ):
                continue
            findings.append(
                FindingRecord(
                    pipeline_run_id=pipeline_run_id,
                    finding_type="corpus_authority_conflict",
                    risk_level=RiskLevel.high,
                    title="Nacrt širi ovlašćenje suprotno korpusu",
                    explanation=(
                        "Nacrt dozvoljava da obeležavanje drveća vrši širok krug "
                        "lica, dok relevantna odredba iz korpusa vezuje tu radnju "
                        "za ovlašćeno preduzeće ili drugo ovlašćeno lice."
                    ),
                    recommendation=(
                        "Uskladiti nacrt sa odredbom iz korpusa: zameniti široku "
                        "formulaciju preciznim ovlašćenim subjektom ili dodati "
                        "izuzetak sa jasnim pravnim osnovom."
                    ),
                    source_legal_unit_id=unit.get("legal_unit_id"),
                    source_path=unit.get("path"),
                    evidence={
                        "draft_quote": content_text,
                        "matched_rule": "tree_marking_authorized_actor",
                        "corpus_conflicts": corpus_units[:3],
                    },
                )
            )
        return findings

    def _authorized_tree_marking_units(
        self, corpus_documents: list[CanonicalDocument]
    ) -> list[dict]:
        matches: list[dict] = []
        for document in corpus_documents:
            for unit in document.canonical_json.get("legal_units", []):
                content_text = unit.get("content_text") or ""
                normalized = _normalize_legal_text(content_text)
                if not (
                    _TREE_MARKING_RE.search(normalized)
                    and _AUTHORIZED_ACTOR_RE.search(normalized)
                ):
                    continue
                matches.append(
                    {
                        "filename": document.filename,
                        "document_type": document.document_type,
                        "title": document.title,
                        "legal_unit_id": unit.get("legal_unit_id"),
                        "path": unit.get("path"),
                        "quote": content_text,
                    }
                )
        return matches


class OverlapChecker:
    """Finds repeated provision wording inside the same draft."""

    def check(
        self,
        *,
        pipeline_run_id: UUID,
        document: CanonicalDocument,
    ) -> list[FindingRecord]:
        seen: dict[str, dict] = {}
        findings: list[FindingRecord] = []
        legal_units = document.canonical_json.get("legal_units", [])
        parent_ids = {
            unit.get("parent_legal_unit_id")
            for unit in legal_units
            if unit.get("parent_legal_unit_id") is not None
        }
        for unit in legal_units:
            if unit.get("legal_unit_id") in parent_ids:
                continue
            content_text = unit.get("content_text") or ""
            normalized = re.sub(r"\s+", " ", content_text.strip().lower())
            if len(normalized) < 30:
                continue
            previous = seen.get(normalized)
            if previous is None:
                seen[normalized] = unit
                continue
            findings.append(
                FindingRecord(
                    pipeline_run_id=pipeline_run_id,
                    finding_type="possible_overlap",
                    risk_level=RiskLevel.low,
                    title="Possible duplicated provision",
                    explanation=(
                        "Two provisions in the draft have the same or nearly same "
                        "wording and may overlap."
                    ),
                    recommendation=(
                        "Merge the provisions or make the scope of each provision "
                        "distinct."
                    ),
                    source_legal_unit_id=unit.get("legal_unit_id"),
                    source_path=unit.get("path"),
                    evidence={
                        "duplicate_of_legal_unit_id": previous.get("legal_unit_id"),
                        "duplicate_of_path": previous.get("path"),
                        "content_text": content_text,
                    },
                )
            )
        return findings


class StaleReferenceChecker:
    """Flags references near text saying that provisions cease to apply."""

    def check(
        self,
        *,
        pipeline_run_id: UUID,
        document: CanonicalDocument,
    ) -> list[FindingRecord]:
        findings: list[FindingRecord] = []
        for unit in document.canonical_json.get("legal_units", []):
            content_text = unit.get("content_text") or ""
            if not _REPEAL_RE.search(content_text.lower()):
                continue
            findings.append(
                FindingRecord(
                    pipeline_run_id=pipeline_run_id,
                    finding_type="reference_stale",
                    risk_level=RiskLevel.medium,
                    title="Reference may point to repealed provisions",
                    explanation=(
                        "The reference text contains a signal that the cited "
                        "provision or act ceases to apply."
                    ),
                    recommendation=(
                        "Verify whether the referenced act or provision is still "
                        "valid before relying on it."
                    ),
                    source_legal_unit_id=unit.get("legal_unit_id"),
                    source_path=unit.get("path"),
                    evidence={"content_text": content_text},
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


@lru_cache
def get_norm_conflict_checker() -> NormConflictChecker:
    return NormConflictChecker()


@lru_cache
def get_corpus_authority_conflict_checker() -> CorpusAuthorityConflictChecker:
    return CorpusAuthorityConflictChecker()


@lru_cache
def get_overlap_checker() -> OverlapChecker:
    return OverlapChecker()


@lru_cache
def get_stale_reference_checker() -> StaleReferenceChecker:
    return StaleReferenceChecker()
