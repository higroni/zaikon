"""Unit tests for the deterministic LLM facade."""

from zaikon.modules.llm.schemas import ExpandQueryRequest, ParseIntentRequest
from zaikon.modules.llm.service import LLMService


def test_llm_service_normalizes_cyrillic_user_intent_query():
    response = LLMService().parse_intent(
        ParseIntentRequest(user_message="Где се помиње Министарство?")
    )

    assert response.intent == "search"
    assert "Gde se pominje Ministarstvo" in response.query


def test_llm_service_expands_legal_query_terms():
    response = LLMService().expand_query(
        ExpandQueryRequest(query="zakon o sumama")
    )

    assert {"zakon", "clan", "stav", "tacka"}.issubset(set(response.terms))
