"""LLM facade with deterministic grounding and optional Ollama provider calls."""

from functools import lru_cache
import re
from typing import Any

import httpx

from zaikon.core.config import settings
from zaikon.core.schemas import ModuleHealth
from zaikon.pipeline.steps.corpus.folder_import import serbian_cyrillic_to_latin
from zaikon.modules.llm.schemas import (
    ExpandQueryRequest,
    ExpandQueryResponse,
    GenerateAnswerRequest,
    GenerateAnswerResponse,
    IntentType,
    ParseIntentRequest,
    ParseIntentResponse,
    SuggestRevisionRequest,
    SuggestRevisionResponse,
)


def _normalize_query(value: str) -> str:
    normalized = (
        serbian_cyrillic_to_latin(value)
        if settings.enable_cyrillic_latin_normalization
        else value
    )
    return re.sub(r"\s+", " ", normalized).strip()


def _terms(value: str) -> list[str]:
    return sorted(
        {token for token in re.findall(r"\w+", value.lower()) if len(token) >= 3}
    )


class OllamaProvider:
    """Small Ollama adapter kept isolated from deterministic grounding logic."""

    def __init__(
        self,
        *,
        base_url: str = settings.llm_base_url,
        model: str = settings.llm_model,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> str | None:
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": settings.llm_temperature,
                        "num_predict": settings.llm_max_tokens,
                    },
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return None
        generated = payload.get("response")
        return generated.strip() if isinstance(generated, str) else None


class LLMService:
    """Grounded helper for intent, query expansion, answers, and revision hints."""

    def __init__(self, provider: OllamaProvider | None = None) -> None:
        self.provider = (
            provider
            if settings.llm_use_provider and settings.llm_provider == "ollama"
            else None
        )

    def health(self) -> ModuleHealth:
        return ModuleHealth(module_name="llm")

    def parse_intent(self, request: ParseIntentRequest) -> ParseIntentResponse:
        query = _normalize_query(request.user_message)
        folded = query.lower()
        intent = IntentType.search
        confidence = 0.68

        if any(term in folded for term in ["objasni", "zasto", "zašto", "zbog cega"]):
            intent = IntentType.explain
            confidence = 0.76
        elif any(
            term in folded
            for term in [
                "predlozi",
                "predloži",
                "preformulisi",
                "preformuliši",
                "izmeni",
            ]
        ):
            intent = IntentType.draft_revision
            confidence = 0.74
        elif not query:
            intent = IntentType.unknown
            confidence = 0.0

        return ParseIntentResponse(
            intent=intent,
            query=query,
            confidence=confidence,
            metadata={"provider": self._provider_name(), "model": settings.llm_model},
        )

    def expand_query(self, request: ExpandQueryRequest) -> ExpandQueryResponse:
        query = _normalize_query(request.query)
        terms = _terms(query)
        expansion_terms = []
        if "zakon" in terms:
            expansion_terms.extend(["clan", "stav", "tacka"])
        if "pravilnik" in terms or "uredba" in terms:
            expansion_terms.extend(["akt", "propis"])

        all_terms = sorted(set(terms + expansion_terms))
        expanded_query = " ".join(all_terms) if all_terms else query
        return ExpandQueryResponse(
            expanded_query=expanded_query,
            terms=all_terms,
            metadata={"provider": "deterministic"},
        )

    def generate_answer(self, request: GenerateAnswerRequest) -> GenerateAnswerResponse:
        question = _normalize_query(request.question)
        citations = request.retrieval_results[:3]
        if not citations:
            return GenerateAnswerResponse(
                answer_text=(
                    "Nisam našao dovoljno utemeljene odredbe u izabranom korpusu "
                    "za ovo pitanje. Probaj uži upit ili proveri da li je korpus importovan."
                ),
                citations=[],
                metadata={
                    "provider": self._provider_name(),
                    "grounded": False,
                    "citation_guard": {
                        "status": "no_citations",
                        "citation_count": 0,
                    },
                },
            )

        deterministic_answer = self._deterministic_answer(question, citations)
        provider_answer = self._provider_answer(question, citations)
        answer_text = provider_answer or deterministic_answer
        citation_guard = self._citation_guard(answer_text, citations)
        return GenerateAnswerResponse(
            answer_text=answer_text,
            citations=citations,
            metadata={
                "provider": self._provider_name(provider_answer_used=bool(provider_answer)),
                "grounded": citation_guard["status"] == "passed",
                "fallback_used": provider_answer is None,
                "citation_guard": citation_guard,
            },
        )

    def suggest_revision(
        self, request: SuggestRevisionRequest
    ) -> SuggestRevisionResponse:
        source_text = _normalize_query(request.source_text)
        instruction = _normalize_query(request.instruction)
        citations = request.evidence[:3]
        suggested_text = source_text
        if citations:
            suggested_text = (
                f"{source_text}\n\n"
                "Predlog usklađivanja: proveriti formulaciju u odnosu na "
                f"{citations[0].filename}, {citations[0].path}."
            )
        return SuggestRevisionResponse(
            suggested_text=suggested_text,
            explanation=(
                "Predlog koristi instrukciju i dostupne citate; "
                f"instrukcija: {instruction}"
            ),
            citations=citations,
        )

    def _deterministic_answer(self, question: str, citations: list[Any]) -> str:
        lines = [
            f"Za pitanje: {question}",
            "",
            "Relevantne odredbe u korpusu:",
        ]
        for index, result in enumerate(citations, start=1):
            quote = result.content_text.strip().replace("\n", " ")
            if len(quote) > 240:
                quote = f"{quote[:237]}..."
            lines.append(f"{index}. {result.filename}, {result.path}: {quote}")
        lines.append("")
        lines.append(
            "Zaključak je informativan i mora ostati vezan za navedene citate; "
            "pravnik treba da potvrdi konačnu ocenu."
        )
        return "\n".join(lines)

    def _provider_answer(self, question: str, citations: list[Any]) -> str | None:
        if self.provider is None:
            return None
        prompt = self._grounded_prompt(question, citations)
        generated = self.provider.generate(prompt)
        if not generated:
            return None
        return f"{generated}\n\nCitati:\n{self._citation_lines(citations)}"

    def _grounded_prompt(self, question: str, citations: list[Any]) -> str:
        return (
            "Odgovori na srpskom latinicom. Koristi samo navedene citate. "
            "Ne iznosi pravni zaključak bez ograde da pravnik mora da potvrdi ocenu.\n\n"
            f"Pitanje: {question}\n\n"
            f"Citati:\n{self._citation_lines(citations)}"
        )

    def _citation_lines(self, citations: list[Any]) -> str:
        lines = []
        for index, result in enumerate(citations, start=1):
            quote = result.content_text.strip().replace("\n", " ")
            if len(quote) > 360:
                quote = f"{quote[:357]}..."
            lines.append(f"{index}. {result.filename}, {result.path}: {quote}")
        return "\n".join(lines)

    def _citation_guard(self, answer_text: str, citations: list[Any]) -> dict[str, Any]:
        if not citations:
            return {"status": "no_citations", "citation_count": 0}
        missing = []
        for result in citations:
            if result.filename not in answer_text and result.path not in answer_text:
                missing.append(
                    {
                        "filename": result.filename,
                        "path": result.path,
                    }
                )
        return {
            "status": "passed" if not missing else "missing_citation_markers",
            "citation_count": len(citations),
            "missing_citations": missing,
        }

    def _provider_name(self, *, provider_answer_used: bool = False) -> str:
        if provider_answer_used:
            return settings.llm_provider
        return "deterministic"


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService(provider=OllamaProvider())
