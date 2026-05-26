"""Rule-based Serbian legal reference extraction."""

from functools import lru_cache
import re

from zaikon.core.schemas import ModuleHealth
from zaikon.modules.references.schemas import (
    ExtractReferencesRequest,
    ExtractReferencesResponse,
    LegalReferenceRecord,
    ResolvedReferenceRecord,
    ResolveReferencesRequest,
    ResolveReferencesResponse,
)


_ARTICLE_REFERENCE_RE = re.compile(
    r"\b(?:clan|član)(?:a|u|om)?\s+(?P<article>\d+[a-z]?)\.?"
    r"(?:\s+stav(?:a|u|om)?\s+(?P<paragraph>\d+[a-z]?)\.?)?"
    r"(?:\s+(?:tack|tačk)(?:a|e|i|om)?\s+(?P<item>\d+[a-z]?)\.?)?",
    re.IGNORECASE,
)
_OFFICIAL_GAZETTE_RE = re.compile(
    r"\b(?:sluzbeni|službeni)\s+glasnik\s+rs\b\s*,?\s*"
    r"(?:broj|br)\.?\s+(?P<number>[\d/]+)",
    re.IGNORECASE,
)


class ReferenceService:
    """Extracts legal references from canonical legal units."""

    def health(self) -> ModuleHealth:
        return ModuleHealth(module_name="references")

    def extract_references(
        self, request: ExtractReferencesRequest
    ) -> ExtractReferencesResponse:
        references: list[LegalReferenceRecord] = []
        legal_units = request.document.canonical_json.get("legal_units", [])
        parent_ids = {
            unit.get("parent_legal_unit_id")
            for unit in legal_units
            if unit.get("parent_legal_unit_id") is not None
        }

        for unit in legal_units:
            if unit.get("legal_unit_id") in parent_ids:
                continue
            content_text = unit.get("content_text") or ""
            source_legal_unit_id = unit.get("legal_unit_id")
            source_path = unit.get("path")

            for match in _ARTICLE_REFERENCE_RE.finditer(content_text):
                references.append(
                    LegalReferenceRecord(
                        source_legal_unit_id=source_legal_unit_id,
                        source_path=source_path,
                        raw_text=match.group(0),
                        reference_type="article_reference",
                        target_article_number=match.group("article"),
                        target_paragraph_number=match.group("paragraph"),
                        target_item_number=match.group("item"),
                        confidence=0.82,
                    )
                )

            for match in _OFFICIAL_GAZETTE_RE.finditer(content_text):
                references.append(
                    LegalReferenceRecord(
                        source_legal_unit_id=source_legal_unit_id,
                        source_path=source_path,
                        raw_text=match.group(0),
                        reference_type="official_gazette_reference",
                        target_document_title="Sluzbeni glasnik RS",
                        confidence=0.78,
                    )
                )

        return ExtractReferencesResponse(references=references)

    def resolve_references(
        self, request: ResolveReferencesRequest
    ) -> ResolveReferencesResponse:
        if request.document is None:
            resolved_references = [
                ResolvedReferenceRecord(
                    reference_id=reference.reference_id,
                    resolution_status="out_of_scope",
                    resolution_note="No canonical document supplied for resolution",
                )
                for reference in request.references
            ]
            return ResolveReferencesResponse(resolved_references=resolved_references)

        units_by_path = {
            unit.get("path"): unit
            for unit in request.document.canonical_json.get("legal_units", [])
        }
        resolved_references = []

        for reference in request.references:
            if reference.reference_type != "article_reference":
                resolved_references.append(
                    ResolvedReferenceRecord(
                        reference_id=reference.reference_id,
                        resolution_status="out_of_scope",
                        resolution_note="Only article references resolve in MVP",
                    )
                )
                continue

            path = f"article:{reference.target_article_number}"
            if reference.target_paragraph_number:
                path = f"{path}/paragraph:{reference.target_paragraph_number}"
            target = units_by_path.get(path)
            if target is None and reference.target_paragraph_number:
                target = units_by_path.get(f"article:{reference.target_article_number}")

            if target is None:
                resolved_references.append(
                    ResolvedReferenceRecord(
                        reference_id=reference.reference_id,
                        resolution_status="missing",
                        resolution_note=f"Target path not found: {path}",
                    )
                )
            else:
                resolved_references.append(
                    ResolvedReferenceRecord(
                        reference_id=reference.reference_id,
                        target_legal_unit_id=target.get("legal_unit_id"),
                        resolution_status="resolved",
                        resolution_note=target.get("path"),
                    )
                )

        return ResolveReferencesResponse(resolved_references=resolved_references)


@lru_cache
def get_reference_service() -> ReferenceService:
    return ReferenceService()
