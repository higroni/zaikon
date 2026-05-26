"""Deterministic LLM facade used until a provider-backed adapter is enabled."""

from functools import lru_cache
import re

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
        {
            token.lower()
            for token in re.findall(r"[A-Za-zČĆŠĐŽčćšđž0-9]+", value)
            if len(token) >= 3
        }
    )


class LLMService:
    """Grounded helper for intent, query expansion, answers, and revision hints."""

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
            for term in ["predlozi", "predloži", "preformulisi", "preformuliši", "izmeni"]
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
            metadata={"provider": "deterministic", "model": settings.llm_model},
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
                metadata={"provider": "deterministic", "grounded": False},
            )

        lines = [
            f"Za pitanje: {question}",
            "",
            "Relevantne odredbe u korpusu:",
        ]
        for index, result in enumerate(citations, start=1):
            quote = result.content_text.strip().replace("\n", " ")
            if len(quote) > 240:
                quote = f"{quote[:237]}..."
            lines.append(
                f"{index}. {result.filename}, {result.path}: {quote}"
            )
        lines.append("")
        lines.append(
            "Zaključak je informativan i mora ostati vezan za navedene citate; "
            "pravnik treba da potvrdi konačnu ocenu."
        )
        return GenerateAnswerResponse(
            answer_text="\n".join(lines),
            citations=citations,
            metadata={"provider": "deterministic", "grounded": True},
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
                "Deterministički predlog koristi instrukciju i dostupne citate; "
                f"instrukcija: {instruction}"
            ),
            citations=citations,
        )


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService()
