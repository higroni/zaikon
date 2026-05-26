"""Reference extraction and resolution schemas."""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from zaikon.modules.canonical.schemas import CanonicalDocument


class LegalReferenceRecord(BaseModel):
    reference_id: UUID = Field(default_factory=uuid4)
    source_legal_unit_id: str | None = None
    source_path: str | None = None
    raw_text: str
    reference_type: str
    target_document_title: str | None = None
    target_article_number: str | None = None
    target_paragraph_number: str | None = None
    target_item_number: str | None = None
    confidence: float


class ExtractReferencesRequest(BaseModel):
    document: CanonicalDocument


class ExtractReferencesResponse(BaseModel):
    references: list[LegalReferenceRecord] = Field(default_factory=list)


class ResolvedReferenceRecord(BaseModel):
    resolved_reference_id: UUID = Field(default_factory=uuid4)
    reference_id: UUID
    target_legal_unit_id: str | None = None
    resolution_status: str
    resolution_note: str | None = None


class ResolveReferencesRequest(BaseModel):
    references: list[LegalReferenceRecord]
    document: CanonicalDocument | None = None


class ResolveReferencesResponse(BaseModel):
    resolved_references: list[ResolvedReferenceRecord] = Field(default_factory=list)
