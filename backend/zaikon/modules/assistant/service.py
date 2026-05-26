"""Interactive legal assistant service."""

from functools import lru_cache
from uuid import UUID

from zaikon.core.time import utc_now
from zaikon.modules.llm.schemas import (
    AssistantMessageRecord,
    AssistantRole,
    AssistantSessionRecord,
    CreateAssistantMessageRequest,
    CreateAssistantMessageResponse,
    CreateAssistantSessionRequest,
    CreateAssistantSessionResponse,
    ExpandQueryRequest,
    GenerateAnswerRequest,
    ParseIntentRequest,
)
from zaikon.modules.llm.service import get_llm_service
from zaikon.modules.retrieval.schemas import HybridSearchRequest
from zaikon.modules.retrieval.service import get_retrieval_service


class AssistantService:
    """Stores assistant sessions and produces grounded deterministic answers."""

    def __init__(self) -> None:
        self._sessions: dict[UUID, AssistantSessionRecord] = {}
        self._messages: dict[UUID, list[AssistantMessageRecord]] = {}

    def create_session(
        self, request: CreateAssistantSessionRequest
    ) -> CreateAssistantSessionResponse:
        title = request.title or "Pravna pretraga"
        session = AssistantSessionRecord(
            title=title,
            language_code=request.language_code,
            selected_corpus_id=request.selected_corpus_id,
            metadata=request.metadata,
        )
        self._sessions[session.session_id] = session
        self._messages[session.session_id] = []
        return CreateAssistantSessionResponse(session=session)

    def get_session(self, session_id: UUID) -> AssistantSessionRecord | None:
        return self._sessions.get(session_id)

    def list_messages(self, session_id: UUID) -> list[AssistantMessageRecord] | None:
        messages = self._messages.get(session_id)
        if messages is None:
            return None
        return list(messages)

    def create_message(
        self, session_id: UUID, request: CreateAssistantMessageRequest
    ) -> CreateAssistantMessageResponse:
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Assistant session not found: {session_id}")

        llm = get_llm_service()
        intent = llm.parse_intent(
            ParseIntentRequest(
                user_message=request.content_text,
                language_code=session.language_code,
                context={"session_id": str(session_id), **request.metadata},
            )
        )
        expansion = llm.expand_query(
            ExpandQueryRequest(
                query=intent.query,
                intent=intent.intent,
                language_code=session.language_code,
            )
        )
        retrieval = get_retrieval_service().hybrid_search(
            HybridSearchRequest(
                query=expansion.expanded_query or intent.query,
                top_k=request.top_k,
                corpus_id=session.selected_corpus_id,
            )
        )
        answer = llm.generate_answer(
            GenerateAnswerRequest(
                question=intent.query,
                retrieval_results=retrieval.results,
                language_code=session.language_code,
                context={
                    "intent": intent.intent.value,
                    "expanded_query": expansion.expanded_query,
                },
            )
        )

        user_message = AssistantMessageRecord(
            session_id=session_id,
            role=AssistantRole.user,
            content_text=request.content_text,
            metadata={
                "intent": intent.intent.value,
                "query": intent.query,
                "confidence": intent.confidence,
            },
        )
        assistant_message = AssistantMessageRecord(
            session_id=session_id,
            role=AssistantRole.assistant,
            content_text=answer.answer_text,
            metadata={
                "intent": intent.intent.value,
                "expanded_query": expansion.expanded_query,
                "retrieval_result_count": len(retrieval.results),
                "citations": [
                    {
                        "document_id": result.document_id,
                        "legal_unit_id": result.legal_unit_id,
                        "path": result.path,
                        "filename": result.filename,
                    }
                    for result in answer.citations
                ],
            },
        )
        self._messages[session_id].extend([user_message, assistant_message])
        session.updated_at = utc_now()
        return CreateAssistantMessageResponse(
            user_message=user_message,
            assistant_message=assistant_message,
            retrieval_results=retrieval.results,
        )


@lru_cache
def get_assistant_service() -> AssistantService:
    return AssistantService()
