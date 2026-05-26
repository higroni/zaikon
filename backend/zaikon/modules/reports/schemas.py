"""Report module schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from zaikon.core.time import utc_now


class GenerateReportRequest(BaseModel):
    pipeline_run_id: UUID
    report_format: str = "markdown"


class ReportRecord(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    pipeline_run_id: UUID
    report_format: str = "markdown"
    title: str
    finding_count: int
    content_text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class GenerateReportResponse(BaseModel):
    report: ReportRecord
