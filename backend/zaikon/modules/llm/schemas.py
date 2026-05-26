"""LLM module request and response schemas."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from zaikon.core.schemas import LanguageCode
from zaikon.core.time import utc_now
from zaikon.modules.retrieval.schemas import RetrievalResult


class AssistantRole(StrEnum):
    user = "user"
    assistant = "assistant"
    system = "system"


class IntentType(StrEnum):
    search = "search"
    explain = "explain"
    draft_revision = "draft_revision"
    unknown = "unknown"


class ParseIntentRequest(BaseModel):
    user_message: str
    language_code: LanguageCode = LanguageCode.sr
    context: dict[str, Any] = Field(default_factory=dict)


class ParseIntentResponse(BaseModel):
    intent: IntentType
    query: str
    confidence: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExpandQueryRequest(BaseModel):
    query: str
    intent: IntentType = IntentType.search
    language_code: LanguageCode = LanguageCode.sr


class ExpandQueryResponse(BaseModel):
    expanded_query: str
    terms: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GenerateAnswerRequest(BaseModel):
    question: str
    retrieval_results: list[RetrievalResult] = Field(default_factory=list)
    language_code: LanguageCode = LanguageCode.sr
    context: dict[str, Any] = Field(default_factory=dict)


class GenerateAnswerResponse(BaseModel):
    answer_text: str
    citations: list[RetrievalResult] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SuggestRevisionRequest(BaseModel):
    source_text: str
    instruction: str
    evidence: list[RetrievalResult] = Field(default_factory=list)
    language_code: LanguageCode = LanguageCode.sr


class SuggestRevisionResponse(BaseModel):
    suggested_text: str
    explanation: str
    citations: list[RetrievalResult] = Field(default_factory=list)


class CreateAssistantSessionRequest(BaseModel):
    title: str | None = None
    language_code: LanguageCode = LanguageCode.sr
    selected_corpus_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AssistantSessionRecord(BaseModel):
    session_id: UUID = Field(default_factory=uuid4)
    title: str
    language_code: LanguageCode = LanguageCode.sr
    selected_corpus_id: UUID | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreateAssistantSessionResponse(BaseModel):
    session: AssistantSessionRecord


class CreateAssistantMessageRequest(BaseModel):
    content_text: str
    top_k: int = 5
    metadata: dict[str, Any] = Field(default_factory=dict)


class AssistantMessageRecord(BaseModel):
    message_id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    role: AssistantRole
    content_text: str
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreateAssistantMessageResponse(BaseModel):
    user_message: AssistantMessageRecord
    assistant_message: AssistantMessageRecord
    retrieval_results: list[RetrievalResult] = Field(default_factory=list)
