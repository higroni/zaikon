"""Corpus module request and response schemas."""

from datetime import datetime
from pathlib import Path
import re
from typing import Any
from uuid import UUID, uuid4
from urllib.parse import unquote, urlparse

from pydantic import BaseModel, Field

from zaikon.core.schemas import JobStatus, LanguageCode
from zaikon.core.time import utc_now


class CorpusRecord(BaseModel):
    corpus_id: UUID = Field(default_factory=uuid4)
    name: str
    description: str | None = None
    language_code: LanguageCode = LanguageCode.sr
    domain: str | None = None
    status: str = "active"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CreateCorpusRequest(BaseModel):
    name: str
    description: str | None = None
    language_code: LanguageCode = LanguageCode.sr
    domain: str | None = None


class CreateCorpusResponse(BaseModel):
    corpus: CorpusRecord


class ImportFolderRequest(BaseModel):
    corpus_id: UUID
    folder_uri: str
    recursive: bool | None = None

    @property
    def folder_path(self) -> Path:
        if self.folder_uri.startswith("file://"):
            parsed = urlparse(self.folder_uri)
            path = unquote(parsed.path)
            if re.match(r"^/[A-Za-z]:/", path):
                path = path[1:]
            if parsed.netloc:
                path = f"//{parsed.netloc}{path}"
            return Path(path)
        return Path(self.folder_uri)


class SourceFileRecord(BaseModel):
    source_file_id: UUID = Field(default_factory=uuid4)
    corpus_id: UUID
    source_uri: str
    filename: str
    file_type: str
    content_hash: str
    size_bytes: int
    import_status: str = JobStatus.pending.value
    document_type: str | None = None
    document_type_confidence: float | None = None
    error_message: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class ImportJobRecord(BaseModel):
    import_job_id: UUID = Field(default_factory=uuid4)
    corpus_id: UUID
    folder_uri: str
    status: JobStatus = JobStatus.pending
    total_files: int = 0
    supported_files: int = 0
    unsupported_files: int = 0
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    error_message: str | None = None


class ImportReport(BaseModel):
    import_job_id: UUID
    corpus_id: UUID
    status: JobStatus
    source_files: list[SourceFileRecord] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
    index_reports: dict[str, Any] = Field(default_factory=dict)
    storage_report: dict[str, Any] | None = None
    pipeline_run_id: str | None = None
    artifact_names: list[str] = Field(default_factory=list)


class ImportFolderResponse(BaseModel):
    import_job: ImportJobRecord
    report: ImportReport


class ImportReportResponse(BaseModel):
    report: ImportReport
