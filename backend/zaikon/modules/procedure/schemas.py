"""Schemas for procedure compliance tracking."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ProcedureCase(BaseModel):
    """Tracks a draft through legislative procedure stages."""

    procedure_case_id: UUID = Field(default_factory=uuid4)
    draft_review_id: UUID | None = None
    draft_title: str
    proposer: str | None = None
    procedure_type: Literal[
        "government_bill", "parliamentary_bill", "regulation", "rulebook"
    ] = "government_bill"
    current_stage: Literal[
        "drafting_and_ria",
        "public_consultation",
        "official_opinions",
        "eu_alignment_package",
        "government_committees",
        "government_adoption",
        "parliamentary_review",
    ] = "drafting_and_ria"
    domain: str | None = None
    eu_relevance: Literal["yes", "no", "unknown"] = "unknown"
    budget_impact: Literal["yes", "no", "unknown"] = "unknown"
    status: Literal["in_progress", "blocked", "ready", "completed"] = "in_progress"
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProcessArtifact(BaseModel):
    """Represents a procedural document (RIA, opinion, alignment table, etc.)."""

    artifact_id: UUID = Field(default_factory=uuid4)
    procedure_case_id: UUID
    artifact_type: Literal[
        "ria",
        "public_debate_program",
        "public_debate_report",
        "rsz_opinion",
        "finance_opinion",
        "mei_opinion",
        "eu_alignment_statement",
        "eu_alignment_table",
        "committee_conclusion",
        "other",
    ]
    source_uri: str | None = None
    title: str
    issuer: str | None = None
    issued_at: datetime | None = None
    status: Literal[
        "missing", "submitted", "positive", "negative", "conditional", "not_required"
    ] = "missing"
    content_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.9


class ProcessRequirement(BaseModel):
    """Defines what artifacts are required at each procedure stage."""

    requirement_id: UUID = Field(default_factory=uuid4)
    procedure_type: str
    stage: str
    required_artifact_type: str
    required_when: dict[str, Any] = Field(default_factory=dict)
    source_reference: dict[str, str] = Field(default_factory=dict)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    severity_if_missing: Literal["high", "medium", "low"] = "high"


class InstitutionalOpinion(BaseModel):
    """Tracks opinions from RSZ, MF, MEI, committees."""

    opinion_id: UUID = Field(default_factory=uuid4)
    procedure_case_id: UUID
    institution: Literal[
        "RSZ", "MF", "MEI", "government_committee", "parliament_committee"
    ]
    opinion_status: Literal["positive", "negative", "conditional", "missing", "unclear"]
    summary: str | None = None
    open_remarks: list[dict[str, Any]] = Field(default_factory=list)
    source_artifact_id: UUID | None = None
    issued_at: datetime | None = None


class AlignmentMatrixRow(BaseModel):
    """Represents one row in EU alignment table."""

    row_id: UUID = Field(default_factory=uuid4)
    procedure_case_id: UUID
    domestic_legal_unit_id: str | None = None
    domestic_path: str | None = None
    eu_source_title: str | None = None
    eu_source_article: str | None = None
    eu_celex: str | None = None
    alignment_status: Literal[
        "fully_aligned",
        "partially_aligned",
        "not_aligned",
        "not_applicable",
        "unclear",
    ] = "unclear"
    comment: str | None = None
    source_artifact_id: UUID | None = None


class ReadinessReport(BaseModel):
    """Summary of procedure case readiness for next stage."""

    procedure_case_id: UUID
    current_stage: str
    next_stage: str | None = None
    readiness_status: Literal["ready", "blocked", "needs_expert", "incomplete"]
    missing_artifacts: list[str] = Field(default_factory=list)
    unresolved_opinions: list[str] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now())

# Made with Bob
