"""Shared schemas used across module boundaries."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from zaikon.core.time import utc_now


class JobStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class StepStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"
    cancelled = "cancelled"


class RiskLevel(StrEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class FindingStatus(StrEnum):
    open = "open"
    accepted = "accepted"
    rejected = "rejected"
    partial = "partial"
    needs_expert_review = "needs_expert_review"


class LanguageCode(StrEnum):
    sr = "sr"
    mk = "mk"


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ResponseEnvelope(BaseModel):
    success: bool = True
    data: dict[str, Any] | list[Any] | None = None
    errors: list[ErrorDetail] = Field(default_factory=list)
    warnings: list[ErrorDetail] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModuleHealth(BaseModel):
    module_name: str
    status: str = "ok"
    version: str = "0.1.0"
    checked_at: datetime = Field(default_factory=utc_now)


class PipelineArtifact(BaseModel):
    artifact_id: UUID = Field(default_factory=uuid4)
    name: str
    artifact_type: str
    payload: dict[str, Any] | list[Any] | str | int | float | bool | None = None
    created_at: datetime = Field(default_factory=utc_now)


class PipelineLogEntry(BaseModel):
    level: str
    message: str
    step_name: str | None = None
    created_at: datetime = Field(default_factory=utc_now)

