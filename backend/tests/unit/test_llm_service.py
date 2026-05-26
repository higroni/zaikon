"""Unit tests for the deterministic LLM facade."""

from zaikon.modules.llm.schemas import (
    ExpandQueryRequest,
    GenerateAnswerRequest,
    ParseIntentRequest,
)
from zaikon.modules.llm.service import LLMService
from zaikon.core.config import settings
from zaikon.modules.retrieval.schemas import RetrievalResult


class FakeProvider:
    def generate(self, prompt: str) -> str:
        assert "Citati:" in prompt
        return "Generisani odgovor zasnovan na citatima."


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


def test_llm_service_generates_grounded_deterministic_answer():
    response = LLMService().generate_answer(
        GenerateAnswerRequest(
            question="Gde se pominju šume?",
            retrieval_results=[
                RetrievalResult(
                    document_id="doc-1",
                    corpus_id="corpus-1",
                    legal_unit_id="unit-1",
                    document_type="law",
                    filename="zakon.txt",
                    unit_type="article",
                    path="article:1",
                    content_text="Šume su dobro od opšteg interesa.",
                    score=1.0,
                )
            ],
        )
    )

    assert response.metadata["provider"] == "deterministic"
    assert response.metadata["grounded"] is True
    assert response.metadata["citation_guard"]["status"] == "passed"
    assert "zakon.txt, article:1" in response.answer_text


def test_llm_service_can_use_enabled_provider_for_grounded_answer():
    previous = settings.llm_use_provider
    settings.llm_use_provider = True
    try:
        response = LLMService(provider=FakeProvider()).generate_answer(
            GenerateAnswerRequest(
                question="Gde se pominju šume?",
                retrieval_results=[
                    RetrievalResult(
                        document_id="doc-1",
                        corpus_id="corpus-1",
                        legal_unit_id="unit-1",
                        document_type="law",
                        filename="zakon.txt",
                        unit_type="article",
                        path="article:1",
                        content_text="Šume su dobro od opšteg interesa.",
                        score=1.0,
                    )
                ],
            )
        )
    finally:
        settings.llm_use_provider = previous

    assert response.metadata["provider"] == "ollama"
    assert response.metadata["fallback_used"] is False
    assert response.metadata["citation_guard"]["status"] == "passed"
    assert "Generisani odgovor" in response.answer_text
    assert "Citati:" in response.answer_text


def test_llm_service_marks_answer_without_citations_as_ungrounded():
    response = LLMService().generate_answer(
        GenerateAnswerRequest(
            question="Gde se pominju šume?",
            retrieval_results=[],
        )
    )

    assert response.metadata["grounded"] is False
    assert response.metadata["citation_guard"] == {
        "status": "no_citations",
        "citation_count": 0,
    }
