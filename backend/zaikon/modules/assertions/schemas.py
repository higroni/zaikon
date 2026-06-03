"""Schemas for extracted normative assertions."""

from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from zaikon.modules.canonical.schemas import CanonicalDocument


class LegalSlot(BaseModel):
    raw: str
    canonical: str
    confidence: float = 0.75
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeadlineSlot(BaseModel):
    raw: str
    value: int
    unit: str = "day"
    calendar_type: str = "calendar_day"
    start_event: str | None = None
    end_event: str | None = None
    confidence: float = 0.8


class NormativeAssertion(BaseModel):
    assertion_id: UUID = Field(default_factory=uuid4)
    document_id: str | None = None
    pipeline_run_id: UUID | None = None
    corpus_id: UUID | None = None
    source_uri: str
    filename: str
    legal_unit_id: str
    source_path: str
    assertion_type: str
    modality: str | None = None
    actor: LegalSlot | None = None
    action: LegalSlot | None = None
    object: LegalSlot | None = None
    domain: LegalSlot | None = None
    deadline: DeadlineSlot | None = None
    condition: LegalSlot | None = None
    exception: LegalSlot | None = None
    sanction: LegalSlot | None = None
    source_quote: str
    confidence: float = 0.7
    slot_confidence: dict[str, float] = Field(default_factory=dict)
    extraction_method: str = "rules"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractAssertionsRequest(BaseModel):
    document: CanonicalDocument
    corpus_id: UUID | None = None
    pipeline_run_id: UUID | None = None
    document_id: str | None = None


class ExtractAssertionsResponse(BaseModel):
    assertions: list[NormativeAssertion]
    metadata: dict[str, Any] = Field(default_factory=dict)
