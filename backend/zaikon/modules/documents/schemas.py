"""Documents module request and response schemas."""

from typing import Any

from pydantic import BaseModel, Field

from zaikon.core.schemas import LanguageCode


class ExtractTextRequest(BaseModel):
    source_uri: str
    filename: str
    file_type: str
    language_code: LanguageCode = LanguageCode.sr


class ExtractedDocument(BaseModel):
    source_uri: str
    filename: str
    file_type: str
    content_text: str
    language_code: LanguageCode = LanguageCode.sr
    extraction_status: str = "completed"
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractTextResponse(BaseModel):
    document: ExtractedDocument


class ClassifyDocumentRequest(BaseModel):
    content_text: str
    filename: str | None = None
    language_code: LanguageCode = LanguageCode.sr


class ClassifyDocumentResponse(BaseModel):
    document_type: str
    confidence: float
    metadata: dict[str, Any] = Field(default_factory=dict)
