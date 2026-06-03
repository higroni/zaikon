"""Conflict type registry schemas."""

from pydantic import BaseModel, Field

from zaikon.modules.checkers.schemas import FindingRecord


class ConflictTypeRecord(BaseModel):
    finding_type: str
    category: str
    default_severity: str = "medium"
    engine_status: str = "needs_expert_review"
    required_slots: list[str] = Field(default_factory=list)
    evidence_required: list[str] = Field(
        default_factory=lambda: ["draft_quote", "corpus_quote", "slot_diffs"]
    )
    description: str | None = None


class ConflictRuleRecord(BaseModel):
    """Extended conflict type record with rule configuration."""
    rule_id: str
    conflict_type: str
    category: str
    severity: str = "medium"
    description: str | None = None
    enabled: bool = True
    operators: list[str] = Field(default_factory=list)


class ConflictTypeRegistryResponse(BaseModel):
    conflict_types: list[ConflictTypeRecord]
    total: int
    categories: list[str]


class ConflictCandidate(BaseModel):
    candidate_id: str
    draft_assertion_id: str
    corpus_assertion_id: str
    score: float
    match_reasons: list[str] = Field(default_factory=list)
    reject_reasons: list[str] = Field(default_factory=list)
    retrieval_method: str = "assertion_slot_match"


class AssertionConflictEvaluation(BaseModel):
    candidates: list[ConflictCandidate] = Field(default_factory=list)
    findings: list[FindingRecord] = Field(default_factory=list)
    trace: dict = Field(default_factory=dict)
