"""Rule-based draft review checkers."""

from functools import lru_cache
from uuid import UUID

from zaikon.core.schemas import RiskLevel
from zaikon.modules.checkers.schemas import FindingRecord
from zaikon.modules.references.schemas import LegalReferenceRecord, ResolvedReferenceRecord


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


@lru_cache
def get_reference_checker() -> ReferenceChecker:
    return ReferenceChecker()

