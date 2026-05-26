"""Draft review request and response schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from zaikon.core.schemas import JobStatus, LanguageCode
from zaikon.core.time import utc_now
from zaikon.modules.checkers.schemas import FindingRecord


class CreateDraftReviewRequest(BaseModel):
    title: str
    content_text: str
    language_code: LanguageCode = LanguageCode.sr
    selected_corpus_id: UUID | None = None


class CreateDraftReviewFromFileRequest(BaseModel):
    source_uri: str
    title: str | None = None
    file_type: str | None = None
    language_code: LanguageCode = LanguageCode.sr
    selected_corpus_id: UUID | None = None


class DraftReviewRecord(BaseModel):
    pipeline_run_id: UUID = Field(default_factory=uuid4)
    title: str
    language_code: LanguageCode = LanguageCode.sr
    selected_corpus_id: UUID | None = None
    status: JobStatus = JobStatus.pending
    finding_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreateDraftReviewResponse(BaseModel):
    draft_review: DraftReviewRecord


class RunDraftReviewResponse(BaseModel):
    draft_review: DraftReviewRecord
    findings: list[FindingRecord] = Field(default_factory=list)


class DraftReviewDetail(BaseModel):
    draft_review: DraftReviewRecord
    content_text: str
    findings: list[FindingRecord] = Field(default_factory=list)
    artifacts: dict[str, Any] = Field(default_factory=dict)
