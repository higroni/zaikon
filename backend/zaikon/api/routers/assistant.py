"""Interactive assistant endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from zaikon.modules.assistant.service import get_assistant_service
from zaikon.modules.llm.schemas import (
    AssistantMessageRecord,
    CreateAssistantMessageRequest,
    CreateAssistantMessageResponse,
    CreateAssistantSessionRequest,
    CreateAssistantSessionResponse,
)

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/sessions", response_model=CreateAssistantSessionResponse)
def create_assistant_session(
    request: CreateAssistantSessionRequest,
) -> CreateAssistantSessionResponse:
    return get_assistant_service().create_session(request)


@router.post(
    "/sessions/{session_id}/messages",
    response_model=CreateAssistantMessageResponse,
)
def create_assistant_message(
    session_id: UUID,
    request: CreateAssistantMessageRequest,
) -> CreateAssistantMessageResponse:
    try:
        return get_assistant_service().create_message(session_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[AssistantMessageRecord],
)
def list_assistant_messages(session_id: UUID) -> list[AssistantMessageRecord]:
    messages = get_assistant_service().list_messages(session_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Assistant session not found")
    return messages
