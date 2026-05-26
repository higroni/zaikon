"""Legal parser module request and response schemas."""

from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from zaikon.core.schemas import LanguageCode


class ParseLegalStructureRequest(BaseModel):
    source_uri: str
    filename: str
    content_text: str
    document_type: str = "unknown"
    language_code: LanguageCode = LanguageCode.sr


class ParsedLegalUnit(BaseModel):
    legal_unit_id: UUID = Field(default_factory=uuid4)
    parent_legal_unit_id: UUID | None = None
    unit_type: str
    number: str | None = None
    ordinal: int
    heading: str | None = None
    content_text: str
    path: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedLegalDocument(BaseModel):
    source_uri: str
    filename: str
    document_type: str = "unknown"
    title: str | None = None
    language_code: LanguageCode = LanguageCode.sr
    legal_units: list[ParsedLegalUnit] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParseLegalStructureResponse(BaseModel):
    document: ParsedLegalDocument
