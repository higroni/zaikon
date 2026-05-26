"""Rule-based Serbian legal reference extraction and resolution."""

from functools import lru_cache
import re
import unicodedata

from zaikon.core.schemas import ModuleHealth
from zaikon.modules.canonical.schemas import CanonicalDocument
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
    r"(?:\s+(?:tack|tačk)(?:a|e|i|om)?\s+(?P<item>\d+[a-z]?)\.?)?"
    r"(?:\s+(?:ovog\s+zakona|zakona\s+o\s+(?P<title>[^.;,\n]+)))?",
    re.IGNORECASE,
)
_OFFICIAL_GAZETTE_RE = re.compile(
    r"\b(?:sluzbeni|službeni)\s+glasnik\s+rs\b\s*,?\s*"
    r"(?:broj|br)\.?\s+(?P<number>[\d/]+)",
    re.IGNORECASE,
)
_LATIN_FOLD = str.maketrans(
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
    }
)


def _fold(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKC", value).translate(_LATIN_FOLD).lower()
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


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
            if unit.get("legal_unit_id") in parent_ids and self._is_container_unit(unit):
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
                        target_document_title=self._target_title(match.group("title")),
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
        if request.document is None and not request.corpus_documents:
            resolved_references = [
                ResolvedReferenceRecord(
                    reference_id=reference.reference_id,
                    resolution_status="out_of_scope",
                    resolution_note="No canonical document supplied for resolution",
                )
                for reference in request.references
            ]
            return ResolveReferencesResponse(resolved_references=resolved_references)

        document_units_by_path = self._units_by_path(request.document)
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

            target = self._resolve_internal(reference, document_units_by_path)
            if target is not None:
                resolved_references.append(
                    ResolvedReferenceRecord(
                        reference_id=reference.reference_id,
                        target_legal_unit_id=target.get("legal_unit_id"),
                        resolution_status="resolved",
                        resolution_note=target.get("path"),
                    )
                )
                continue

            corpus_target = self._resolve_in_corpus(
                reference=reference,
                corpus_documents=request.corpus_documents,
            )
            if corpus_target is not None:
                document, unit = corpus_target
                resolved_references.append(
                    ResolvedReferenceRecord(
                        reference_id=reference.reference_id,
                        target_legal_unit_id=unit.get("legal_unit_id"),
                        resolution_status="resolved",
                        resolution_note=(
                            f"{document.title or document.filename}: {unit.get('path')}"
                        ),
                    )
                )
                continue

            path = self._target_path_for_reference(reference, document_units_by_path)
            resolved_references.append(
                ResolvedReferenceRecord(
                    reference_id=reference.reference_id,
                    resolution_status="missing",
                    resolution_note=f"Target path not found: {path}",
                )
            )

        return ResolveReferencesResponse(resolved_references=resolved_references)

    def _target_title(self, title_fragment: str | None) -> str | None:
        if not title_fragment:
            return None
        title = title_fragment.strip(" :;,.")
        if not title:
            return None
        return f"Zakon o {title}"

    def _units_by_path(self, document: CanonicalDocument | None) -> dict:
        if document is None:
            return {}
        return {
            unit.get("path"): unit
            for unit in document.canonical_json.get("legal_units", [])
        }

    def _resolve_internal(
        self,
        reference: LegalReferenceRecord,
        units_by_path: dict,
    ) -> dict | None:
        target = units_by_path.get(self._target_path_for_reference(reference, units_by_path))
        return target

    def _resolve_in_corpus(
        self,
        *,
        reference: LegalReferenceRecord,
        corpus_documents: list[CanonicalDocument],
    ) -> tuple[CanonicalDocument, dict] | None:
        if not reference.target_document_title:
            return None
        folded_target_title = _fold(reference.target_document_title)
        candidates = [
            document
            for document in corpus_documents
            if folded_target_title
            and (
                folded_target_title in _fold(document.title)
                or folded_target_title in _fold(document.filename)
            )
        ]
        for document in candidates:
            units_by_path = self._units_by_path(document)
            unit = self._resolve_internal(reference, units_by_path)
            if unit is not None:
                return document, unit
        return None

    def _is_container_unit(self, unit: dict) -> bool:
        unit_type = unit.get("unit_type")
        if unit_type in {"article", "section"}:
            return True
        path = unit.get("path")
        if not isinstance(path, str):
            return False
        return (
            path.startswith("article:")
            and "/" not in path
            or path.startswith("section:")
            and "/" not in path
        )

    def _target_path_for_reference(
        self,
        reference: LegalReferenceRecord,
        units_by_path: dict,
    ) -> str:
        article_path = f"article:{reference.target_article_number}"
        paragraph_path = article_path
        if reference.target_paragraph_number:
            paragraph_path = (
                f"{article_path}/paragraph:{reference.target_paragraph_number}"
            )
        if reference.target_item_number:
            if reference.target_paragraph_number:
                return f"{paragraph_path}/item:{reference.target_item_number}"
            item_path = self._find_item_path_in_article(
                article_path=article_path,
                item_number=reference.target_item_number,
                units_by_path=units_by_path,
            )
            if item_path is not None:
                return item_path
            return f"{article_path}/item:{reference.target_item_number}"
        return paragraph_path

    def _find_item_path_in_article(
        self,
        *,
        article_path: str,
        item_number: str,
        units_by_path: dict,
    ) -> str | None:
        candidates = [
            path
            for path, unit in units_by_path.items()
            if isinstance(path, str)
            and path.startswith(f"{article_path}/")
            and path.endswith(f"/item:{item_number}")
            and unit.get("unit_type") == "item"
        ]
        if len(candidates) == 1:
            return candidates[0]
        return None


@lru_cache
def get_reference_service() -> ReferenceService:
    return ReferenceService()
