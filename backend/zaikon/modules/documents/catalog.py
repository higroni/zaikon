"""Read-only catalog over persisted document artifacts."""

import json
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, Field

from zaikon.core.config import settings


class DocumentSummary(BaseModel):
    document_id: UUID
    corpus_id: UUID | None = None
    source_uri: str
    filename: str
    document_type: str
    title: str | None = None
    canonical_unit_count: int = 0
    import_job_id: UUID


class DocumentDetail(DocumentSummary):
    canonical_json: dict = Field(default_factory=dict)


class LegalUnitRecord(BaseModel):
    legal_unit_id: str
    document_id: UUID
    unit_type: str
    number: str | None = None
    ordinal: int
    heading: str | None = None
    content_text: str
    path: str
    metadata: dict = Field(default_factory=dict)


class DocumentCatalogService:
    """Lists imported documents and legal units from stored pipeline artifacts."""

    def __init__(self, artifact_dir: Path | None = None) -> None:
        self.root = Path(artifact_dir or settings.artifact_dir)
        self.pipeline_artifact_dir = (
            self.root / "corpus" / "pipeline_artifacts"
        )

    def list_documents(self) -> list[DocumentSummary]:
        return [
            self._summary_from_record(import_job_id, record)
            for import_job_id, record, _ in self._iter_document_records()
        ]

    def get_document(self, document_id: UUID) -> DocumentDetail | None:
        for import_job_id, record, canonical_document in self._iter_document_records():
            if str(document_id) != record.get("document_id"):
                continue
            summary = self._summary_from_record(import_job_id, record)
            return DocumentDetail(
                **summary.model_dump(),
                canonical_json=canonical_document.get("canonical_json", {}),
            )
        return None

    def get_legal_unit(self, legal_unit_id: str) -> LegalUnitRecord | None:
        for import_job_id, record, canonical_document in self._iter_document_records():
            document_id = UUID(
                record.get("document_id")
                or str(uuid5(NAMESPACE_URL, record["source_uri"]))
            )
            for unit in canonical_document.get("canonical_json", {}).get(
                "legal_units", []
            ):
                if unit.get("legal_unit_id") != legal_unit_id:
                    continue
                return LegalUnitRecord(
                    document_id=document_id,
                    legal_unit_id=unit["legal_unit_id"],
                    unit_type=unit["unit_type"],
                    number=unit.get("number"),
                    ordinal=unit["ordinal"],
                    heading=unit.get("heading"),
                    content_text=unit.get("content_text") or "",
                    path=unit["path"],
                    metadata=unit.get("metadata", {}),
                )
        return None

    def _iter_document_records(self):
        if not self.pipeline_artifact_dir.exists():
            return
        for import_job_dir in self.pipeline_artifact_dir.iterdir():
            if not import_job_dir.is_dir():
                continue
            stored_report = self._load_artifact_payload(
                import_job_dir / "stored_documents_report.json"
            )
            canonical_documents = self._load_artifact_payload(
                import_job_dir / "canonical_documents.json"
            )
            if not stored_report or not canonical_documents:
                continue
            canonical_by_source_uri = {
                document["source_uri"]: document for document in canonical_documents
            }
            for record in stored_report.get("stored_documents", []):
                canonical_document = canonical_by_source_uri.get(record["source_uri"])
                if canonical_document is None:
                    continue
                yield UUID(import_job_dir.name), record, canonical_document

    def _summary_from_record(self, import_job_id: UUID, record: dict) -> DocumentSummary:
        document_id = record.get("document_id") or str(
            uuid5(NAMESPACE_URL, record["source_uri"])
        )
        return DocumentSummary(
            document_id=UUID(document_id),
            corpus_id=UUID(record["corpus_id"]) if record.get("corpus_id") else None,
            source_uri=record["source_uri"],
            filename=record["filename"],
            document_type=record["document_type"],
            title=record.get("title"),
            canonical_unit_count=record.get("canonical_unit_count", 0),
            import_job_id=import_job_id,
        )

    def _load_artifact_payload(self, path: Path):
        if not path.exists():
            return None
        artifact = json.loads(path.read_text(encoding="utf-8"))
        return artifact.get("payload")
