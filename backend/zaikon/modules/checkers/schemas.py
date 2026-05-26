"""Checker module schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from zaikon.core.schemas import FindingStatus, RiskLevel
from zaikon.core.time import utc_now


class FindingRecord(BaseModel):
    finding_id: UUID = Field(default_factory=uuid4)
    pipeline_run_id: UUID
    finding_type: str
    risk_level: RiskLevel
    status: FindingStatus = FindingStatus.open
    title: str
    explanation: str
    recommendation: str | None = None
    source_legal_unit_id: str | None = None
    source_path: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime | None = None
    review_note: str | None = None


class UpdateFindingReviewDecisionRequest(BaseModel):
    status: FindingStatus
    review_note: str | None = None


class UpdateFindingReviewDecisionResponse(BaseModel):
    finding: FindingRecord
