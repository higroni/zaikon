"""Evaluation harness schemas."""

from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EvaluationExpectedFinding(BaseModel):
    finding_type: str
    risk_level: str | None = None
    required_draft_terms: list[str] = Field(default_factory=list)
    required_corpus_terms: list[str] = Field(default_factory=list)


class EvaluationCorpusDocument(BaseModel):
    filename: str
    text: str


class EvaluationDraft(BaseModel):
    title: str
    text: str


class EvaluationCase(BaseModel):
    case_id: str
    title: str
    domain: str | None = None
    draft: EvaluationDraft
    corpus_documents: list[EvaluationCorpusDocument]
    expected_findings: list[EvaluationExpectedFinding]


class EvaluationCaseResult(BaseModel):
    case_id: str
    title: str
    passed: bool
    expected_finding_types: list[str]
    actual_finding_types: list[str]
    missing_finding_types: list[str]
    pipeline_run_id: str | None = None
    corpus_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class EvaluationRunResponse(BaseModel):
    evaluation_run_id: UUID = Field(default_factory=uuid4)
    passed: bool
    total_cases: int
    passed_cases: int
    failed_cases: int
    results: list[EvaluationCaseResult]
    metrics: dict[str, Any] = Field(default_factory=dict)


class MetricsReport(BaseModel):
    """Precision/Recall metrics for conflict detection."""
    
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    total_expected: int = 0
    total_actual: int = 0
    per_type_metrics: dict[str, dict[str, float]] = Field(default_factory=dict)
    confusion_matrix: dict[str, Any] = Field(default_factory=dict)
