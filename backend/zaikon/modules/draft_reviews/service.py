"""Draft review service."""

import json
from pathlib import Path
from uuid import UUID

from zaikon.core.config import settings
from zaikon.core.schemas import FindingStatus, JobStatus
from zaikon.core.time import utc_now
from zaikon.modules.canonical.schemas import CanonicalDocument
from zaikon.modules.canonical.schemas import CanonicalizeRequest
from zaikon.modules.canonical.schemas import ExportAkomaNtosoRequest
from zaikon.modules.canonical.service import get_canonical_service
from zaikon.modules.checkers.schemas import FindingRecord
from zaikon.modules.checkers.service import get_definition_consistency_checker
from zaikon.modules.checkers.service import get_reference_checker
from zaikon.modules.checkers.service import get_temporal_validity_checker
from zaikon.modules.checkers.service import get_terminology_consistency_checker
from zaikon.modules.documents.schemas import ClassifyDocumentRequest
from zaikon.modules.documents.schemas import ExtractTextRequest
from zaikon.modules.documents.service import get_document_service
from zaikon.modules.documents.service import path_from_uri
from zaikon.modules.draft_reviews.schemas import (
    CreateDraftReviewFromFileRequest,
    CreateDraftReviewRequest,
    CreateDraftReviewResponse,
    DraftReviewDetail,
    DraftReviewRecord,
    RunDraftReviewResponse,
)
from zaikon.modules.legal_parser.schemas import ParseLegalStructureRequest
from zaikon.modules.legal_parser.service import get_legal_parser_service
from zaikon.modules.references.schemas import (
    ExtractReferencesRequest,
    ResolveReferencesRequest,
)
from zaikon.modules.references.service import get_reference_service
from zaikon.modules.retrieval.schemas import HybridSearchRequest
from zaikon.modules.retrieval.service import get_retrieval_service
from zaikon.pipeline.steps.corpus.folder_import import serbian_cyrillic_to_latin


class DraftReviewService:
    """Stores and runs rule-based review jobs for draft legal text."""

    def __init__(self, artifact_dir: Path | None = None) -> None:
        self.root = Path(artifact_dir or settings.artifact_dir) / "draft_reviews"
        self.root.mkdir(parents=True, exist_ok=True)
        self.records_path = self.root / "draft_reviews.json"
        self.content_dir = self.root / "content"
        self.finding_dir = self.root / "findings"
        self.artifact_dir = self.root / "artifacts"
        self.content_dir.mkdir(parents=True, exist_ok=True)
        self.finding_dir.mkdir(parents=True, exist_ok=True)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self._records = self._load_records()

    def create_draft_review(
        self, request: CreateDraftReviewRequest
    ) -> CreateDraftReviewResponse:
        return self._create_record(
            title=request.title,
            content_text=request.content_text,
            language_code=request.language_code,
            selected_corpus_id=request.selected_corpus_id,
            metadata={"input_type": "text"},
        )

    def create_draft_review_from_file(
        self, request: CreateDraftReviewFromFileRequest
    ) -> CreateDraftReviewResponse:
        path = path_from_uri(request.source_uri)
        file_type = (request.file_type or path.suffix.lstrip(".")).lower()
        if file_type not in {"txt", "pdf", "docx"}:
            raise ValueError(f"Unsupported draft file_type: {file_type}")
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Draft file not found: {request.source_uri}")

        extracted = get_document_service().extract_text(
            ExtractTextRequest(
                source_uri=request.source_uri,
                filename=path.name,
                file_type=file_type,
                language_code=request.language_code,
            )
        )
        return self._create_record(
            title=request.title or path.stem,
            content_text=extracted.document.content_text,
            language_code=request.language_code,
            selected_corpus_id=request.selected_corpus_id,
            metadata={
                "input_type": "file",
                "source_uri": request.source_uri,
                "filename": path.name,
                "file_type": file_type,
                "extraction": extracted.document.metadata,
            },
        )

    def _create_record(
        self,
        *,
        title: str,
        content_text: str,
        language_code,
        selected_corpus_id: UUID | None,
        metadata: dict,
    ) -> CreateDraftReviewResponse:
        record = DraftReviewRecord(
            title=title,
            language_code=language_code,
            selected_corpus_id=selected_corpus_id,
            metadata=metadata,
        )
        self._records[record.pipeline_run_id] = record
        self._write_json(
            self.content_dir / f"{record.pipeline_run_id}.json",
            {"content_text": content_text},
        )
        self._save_records()
        return CreateDraftReviewResponse(draft_review=record)

    def list_draft_reviews(self) -> list[DraftReviewRecord]:
        return sorted(
            self._records.values(), key=lambda record: record.created_at, reverse=True
        )

    def get_draft_review(self, pipeline_run_id: UUID) -> DraftReviewDetail | None:
        record = self._records.get(pipeline_run_id)
        if record is None:
            return None
        return DraftReviewDetail(
            draft_review=record,
            content_text=self._load_content(pipeline_run_id),
            findings=self.list_findings(pipeline_run_id),
            artifacts=self._load_artifacts(pipeline_run_id),
        )

    def export_akoma_ntoso(self, pipeline_run_id: UUID) -> str | None:
        if pipeline_run_id not in self._records:
            return None
        artifacts = self._load_artifacts(pipeline_run_id)
        canonical_payload = artifacts.get("canonical_document")
        if canonical_payload is None:
            return None
        canonical_document = CanonicalDocument.model_validate(canonical_payload)
        response = get_canonical_service().export_akoma_ntoso(
            ExportAkomaNtosoRequest(document=canonical_document)
        )
        return response.xml_text

    def list_artifacts(self, pipeline_run_id: UUID) -> list[str] | None:
        if pipeline_run_id not in self._records:
            return None
        return sorted(self._load_artifacts(pipeline_run_id))

    def get_artifact(self, pipeline_run_id: UUID, artifact_name: str):
        if pipeline_run_id not in self._records:
            return None
        artifacts = self._load_artifacts(pipeline_run_id)
        return artifacts.get(artifact_name)

    def list_findings(self, pipeline_run_id: UUID) -> list[FindingRecord]:
        path = self.finding_dir / f"{pipeline_run_id}.json"
        payload = self._read_json(path, [])
        return [FindingRecord.model_validate(item) for item in payload]

    def list_all_findings(
        self,
        *,
        pipeline_run_id: UUID | None = None,
        status: FindingStatus | None = None,
    ) -> list[FindingRecord]:
        paths = (
            [self.finding_dir / f"{pipeline_run_id}.json"]
            if pipeline_run_id is not None
            else list(self.finding_dir.glob("*.json"))
        )
        findings = []
        for path in paths:
            if not path.exists():
                continue
            findings.extend(self._load_findings_path(path))
        if status is not None:
            findings = [finding for finding in findings if finding.status == status]
        return sorted(findings, key=lambda finding: finding.created_at, reverse=True)

    def get_finding(self, finding_id: UUID) -> FindingRecord | None:
        for path in self.finding_dir.glob("*.json"):
            for finding in self._load_findings_path(path):
                if finding.finding_id == finding_id:
                    return finding
        return None

    def update_finding_review_decision(
        self,
        finding_id: UUID,
        status: FindingStatus,
        review_note: str | None = None,
    ) -> FindingRecord | None:
        for path in self.finding_dir.glob("*.json"):
            findings = self._load_findings_path(path)
            for index, finding in enumerate(findings):
                if finding.finding_id != finding_id:
                    continue
                findings[index] = finding.model_copy(
                    update={
                        "status": status,
                        "review_note": review_note,
                        "updated_at": utc_now(),
                    }
                )
                self._write_json(
                    path,
                    [item.model_dump(mode="json") for item in findings],
                )
                return findings[index]
        return None

    def run_draft_review(self, pipeline_run_id: UUID) -> RunDraftReviewResponse:
        record = self._records.get(pipeline_run_id)
        if record is None:
            raise KeyError(f"Draft review not found: {pipeline_run_id}")

        record.status = JobStatus.running
        record.updated_at = utc_now()
        self._save_records()

        try:
            content_text = self._load_content(pipeline_run_id)
            normalized_text = (
                serbian_cyrillic_to_latin(content_text)
                if settings.enable_cyrillic_latin_normalization
                else content_text
            )
            document_type = get_document_service().classify_document(
                ClassifyDocumentRequest(
                    content_text=normalized_text,
                    filename=self._filename_for_record(record),
                    language_code=record.language_code,
                )
            )
            parsed = get_legal_parser_service().parse_legal_structure(
                ParseLegalStructureRequest(
                    source_uri=f"draft-review://{pipeline_run_id}",
                    filename=self._filename_for_record(record),
                    content_text=normalized_text,
                    document_type=document_type.document_type,
                    language_code=record.language_code,
                )
            )
            canonical = get_canonical_service().to_canonical_json(
                CanonicalizeRequest(document=parsed.document)
            )
            references = get_reference_service().extract_references(
                ExtractReferencesRequest(document=canonical.document)
            )
            resolved = get_reference_service().resolve_references(
                ResolveReferencesRequest(
                    references=references.references,
                    document=canonical.document,
                )
            )
            findings = get_reference_checker().check(
                pipeline_run_id=pipeline_run_id,
                references=references.references,
                resolved_references=resolved.resolved_references,
            )
            findings.extend(
                get_definition_consistency_checker().check(
                    pipeline_run_id=pipeline_run_id,
                    document=canonical.document,
                )
            )
            findings.extend(
                get_terminology_consistency_checker().check(
                    pipeline_run_id=pipeline_run_id,
                    document=canonical.document,
                )
            )
            findings.extend(
                get_temporal_validity_checker().check(
                    pipeline_run_id=pipeline_run_id,
                    document=canonical.document,
                )
            )
            retrieval_results = self._retrieve_related_corpus_units(
                record=record,
                query=normalized_text,
            )
            findings = self._attach_retrieval_evidence(
                findings=findings,
                retrieval_results=retrieval_results,
            )

            self._save_findings(pipeline_run_id, findings)
            self._save_artifacts(
                pipeline_run_id,
                {
                    "normalized_text": normalized_text,
                    "classification": document_type.model_dump(mode="json"),
                    "parsed_document": parsed.document.model_dump(mode="json"),
                    "canonical_document": canonical.document.model_dump(mode="json"),
                    "references": references.model_dump(mode="json"),
                    "resolved_references": resolved.model_dump(mode="json"),
                    "retrieval_results": retrieval_results,
                },
            )
            record.status = JobStatus.completed
            record.finding_count = len(findings)
            record.updated_at = utc_now()
            record.metadata = {
                **record.metadata,
                "document_type": document_type.document_type,
                "classification_confidence": document_type.confidence,
                "reference_count": len(references.references),
                "resolved_reference_count": len(resolved.resolved_references),
                "retrieval_result_count": len(retrieval_results),
            }
            self._save_records()
            return RunDraftReviewResponse(draft_review=record, findings=findings)
        except Exception:
            record.status = JobStatus.failed
            record.updated_at = utc_now()
            self._save_records()
            raise

    def _load_records(self) -> dict[UUID, DraftReviewRecord]:
        payload = self._read_json(self.records_path, [])
        records = [DraftReviewRecord.model_validate(item) for item in payload]
        return {record.pipeline_run_id: record for record in records}

    def _save_records(self) -> None:
        self._write_json(
            self.records_path,
            [record.model_dump(mode="json") for record in self._records.values()],
        )

    def _load_content(self, pipeline_run_id: UUID) -> str:
        payload = self._read_json(
            self.content_dir / f"{pipeline_run_id}.json",
            {"content_text": ""},
        )
        return payload["content_text"]

    def _filename_for_record(self, record: DraftReviewRecord) -> str:
        filename = record.metadata.get("filename")
        if isinstance(filename, str) and filename:
            return filename
        return f"{record.title}.txt"

    def _retrieve_related_corpus_units(
        self,
        *,
        record: DraftReviewRecord,
        query: str,
    ) -> list[dict]:
        if record.selected_corpus_id is None:
            return []
        response = get_retrieval_service().hybrid_search(
            HybridSearchRequest(
                query=query,
                top_k=5,
                corpus_id=record.selected_corpus_id,
            )
        )
        return [result.model_dump(mode="json") for result in response.results]

    def _attach_retrieval_evidence(
        self,
        *,
        findings: list[FindingRecord],
        retrieval_results: list[dict],
    ) -> list[FindingRecord]:
        if not retrieval_results:
            return findings
        related_legal_units = [
            {
                "document_id": result["document_id"],
                "corpus_id": result.get("corpus_id"),
                "legal_unit_id": result["legal_unit_id"],
                "filename": result["filename"],
                "document_type": result["document_type"],
                "unit_type": result["unit_type"],
                "path": result["path"],
                "score": result["score"],
                "matched_terms": result.get("metadata", {}).get("matched_terms", []),
                "quote": result["content_text"][:500],
            }
            for result in retrieval_results[:3]
        ]
        return [
            finding.model_copy(
                update={
                    "evidence": {
                        **finding.evidence,
                        "related_legal_units": related_legal_units,
                    }
                }
            )
            for finding in findings
        ]

    def _save_findings(
        self, pipeline_run_id: UUID, findings: list[FindingRecord]
    ) -> None:
        self._write_json(
            self.finding_dir / f"{pipeline_run_id}.json",
            [finding.model_dump(mode="json") for finding in findings],
        )

    def _load_findings_path(self, path: Path) -> list[FindingRecord]:
        payload = self._read_json(path, [])
        return [FindingRecord.model_validate(item) for item in payload]

    def _save_artifacts(self, pipeline_run_id: UUID, artifacts: dict) -> None:
        self._write_json(self.artifact_dir / f"{pipeline_run_id}.json", artifacts)

    def _load_artifacts(self, pipeline_run_id: UUID) -> dict:
        return self._read_json(self.artifact_dir / f"{pipeline_run_id}.json", {})

    def _read_json(self, path: Path, default):
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )


def get_draft_review_service() -> DraftReviewService:
    return DraftReviewService()
