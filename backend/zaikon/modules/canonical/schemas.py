"""Canonical module request and response schemas."""

from typing import Any

from pydantic import BaseModel, Field

from zaikon.core.schemas import LanguageCode
from zaikon.modules.legal_parser.schemas import ParsedLegalDocument


class CanonicalizeRequest(BaseModel):
    document: ParsedLegalDocument


class CanonicalDocument(BaseModel):
    source_uri: str
    filename: str
    document_type: str
    title: str | None = None
    language_code: LanguageCode = LanguageCode.sr
    canonical_json: dict[str, Any] = Field(default_factory=dict)


class CanonicalizeResponse(BaseModel):
    document: CanonicalDocument


class ExportAkomaNtosoRequest(BaseModel):
    document: CanonicalDocument


class ExportAkomaNtosoResponse(BaseModel):
    xml_text: str
