"""Rule-based extraction of normative assertions from canonical documents."""

from functools import lru_cache
import logging
import re
from uuid import NAMESPACE_URL, UUID, uuid5

from zaikon.core.config import settings
from zaikon.modules.assertions.schemas import (
    DeadlineSlot,
    ExtractAssertionsRequest,
    ExtractAssertionsResponse,
    LegalSlot,
    NormativeAssertion,
)
from zaikon.modules.canonical.schemas import CanonicalDocument
from zaikon.modules.ontology.schemas import OntologyMatch
from zaikon.modules.ontology.service import get_ontology_service, normalize_legal_text

logger = logging.getLogger(__name__)


_DEADLINE_RE = re.compile(
    r"\b(?:u\s+roku\s+od|najkasnije\s+u\s+roku\s+od|rok\s+je)\s+"
    r"(?P<value>\d+|jedan|jednog|dva|tri|cetiri|pet|sest|sedam|osam|devet|deset|"
    r"petnaest|trideset)\s+(?P<working>radnih\s+)?dan(?:a)?\b",
    re.IGNORECASE,
)
_NUMBER_WORDS = {
    "jedan": 1,
    "jednog": 1,
    "dva": 2,
    "tri": 3,
    "cetiri": 4,
    "pet": 5,
    "sest": 6,
    "sedam": 7,
    "osam": 8,
    "devet": 9,
    "deset": 10,
    "petnaest": 15,
    "trideset": 30,
}
_PROHIBITION_RE = re.compile(r"\b(?:ne\s+sme|zabranjuje\s+se|zabranjeno)\b")
_OBLIGATION_RE = re.compile(r"\b(?:mora|duzan|duzna|duzno|obavezan|obavezna)\b")
_PERMISSION_RE = re.compile(r"\b(?:moze|mogu|ima\s+pravo)\b")
_COMPETENCE_RE = re.compile(
    r"\b(?:nadlezan|nadlezna|nadlezno|vrsi\s+kontrolu|kontrolu\s+.+\s+vrsi|"
    r"vrsi\s+nadzor|inspekcijski\s+nadzor)\b"
)
_AUTHORIZATION_RE = re.compile(r"\b(?:ovlascen|ovlascena|ovlasceno|ovlasceni)\b")


class AssertionExtractionService:
    """Extracts a first-pass structured assertion layer from legal units."""

    def extract_assertions(
        self, request: ExtractAssertionsRequest
    ) -> ExtractAssertionsResponse:
        assertions = self.extract_from_document(
            document=request.document,
            corpus_id=request.corpus_id,
            pipeline_run_id=request.pipeline_run_id,
            document_id=request.document_id,
        )
        return ExtractAssertionsResponse(
            assertions=assertions,
            metadata={"assertion_count": len(assertions), "extractor": "rules"},
        )

    def extract_from_document(
        self,
        *,
        document: CanonicalDocument,
        corpus_id: UUID | None = None,
        pipeline_run_id: UUID | None = None,
        document_id: str | None = None,
    ) -> list[NormativeAssertion]:
        assertions: list[NormativeAssertion] = []
        for unit in document.canonical_json.get("legal_units", []):
            content_text = (unit.get("content_text") or "").strip()
            if len(content_text) < 8:
                continue
            extracted = self._extract_unit_assertions(
                document=document,
                unit=unit,
                content_text=content_text,
                corpus_id=corpus_id,
                pipeline_run_id=pipeline_run_id,
                document_id=document_id,
            )
            assertions.extend(extracted)
        return assertions

    def _extract_unit_assertions(
        self,
        *,
        document: CanonicalDocument,
        unit: dict,
        content_text: str,
        corpus_id: UUID | None,
        pipeline_run_id: UUID | None,
        document_id: str | None,
    ) -> list[NormativeAssertion]:
        segments = self._segments(content_text)
        if len(segments) > 1:
            assertions: list[NormativeAssertion] = []
            for segment in segments:
                assertions.extend(
                    self._extract_unit_assertions(
                        document=document,
                        unit=unit,
                        content_text=segment,
                        corpus_id=corpus_id,
                        pipeline_run_id=pipeline_run_id,
                        document_id=document_id,
                    )
                )
            return assertions

        ontology = get_ontology_service()
        normalized = normalize_legal_text(content_text)
        
        # Try ontology first (fast, precise)
        actor = self._slot(ontology.match_actor(content_text))
        action = self._slot(ontology.match_action(content_text))
        obj = self._slot(ontology.match_object(content_text))
        
        # Fallback to NER if ontology didn't find slots
        if settings.ner_enabled and settings.ner_fallback_to_ontology:
            if actor is None or action is None or obj is None:
                try:
                    from zaikon.modules.ner.service import get_ner_service
                    from zaikon.modules.ontology.auto_learning_service import get_auto_learning_service
                    
                    ner_service = get_ner_service()
                    auto_learning = get_auto_learning_service()
                    
                    if ner_service.is_enabled():
                        ner_result = ner_service.extract(content_text)
                        
                        # Use NER results if ontology didn't find anything
                        if actor is None and ner_result.actors:
                            # Use first actor with highest confidence
                            best_actor = max(ner_result.actors, key=lambda x: x.confidence)
                            actor = LegalSlot(
                                raw=best_actor.text,
                                canonical=best_actor.lemma,
                                confidence=best_actor.confidence
                            )
                            # Learn from NER extraction
                            auto_learning.learn_from_ner_slot(best_actor, "actor")
                        
                        if action is None and ner_result.actions:
                            best_action = max(ner_result.actions, key=lambda x: x.confidence)
                            action = LegalSlot(
                                raw=best_action.text,
                                canonical=best_action.lemma,
                                confidence=best_action.confidence
                            )
                            # Learn from NER extraction
                            auto_learning.learn_from_ner_slot(best_action, "action")
                        
                        if obj is None and ner_result.objects:
                            best_obj = max(ner_result.objects, key=lambda x: x.confidence)
                            obj = LegalSlot(
                                raw=best_obj.text,
                                canonical=best_obj.lemma,
                                confidence=best_obj.confidence
                            )
                            # Learn from NER extraction
                            auto_learning.learn_from_ner_slot(best_obj, "object")
                except Exception as e:
                    logger.warning(f"NER extraction failed, using ontology only: {e}")
        
        # Legacy fallback for "kontrola"
        if action is None and "kontrol" in normalized:
            action = LegalSlot(raw="kontrola", canonical="inspect", confidence=0.74)
        domain = self._domain_slot(content_text, actor, obj)
        deadline = self._deadline(content_text)
        modality = self._modality(normalized)
        assertion_type = self._assertion_type(
            normalized=normalized,
            modality=modality,
            action=action,
            deadline=deadline,
        )

        if not assertion_type and not deadline:
            return []

        if assertion_type is None:
            assertion_type = "deadline"

        assertion = NormativeAssertion(
            assertion_id=self._assertion_id(
                source_uri=document.source_uri,
                legal_unit_id=str(unit.get("legal_unit_id")),
                assertion_type=assertion_type,
                source_quote=content_text,
            ),
            document_id=document_id,
            pipeline_run_id=pipeline_run_id,
            corpus_id=corpus_id,
            source_uri=document.source_uri,
            filename=document.filename,
            legal_unit_id=str(unit.get("legal_unit_id")),
            source_path=str(unit.get("path")),
            assertion_type=assertion_type,
            modality=modality,
            actor=actor,
            action=action,
            object=obj,
            domain=domain,
            deadline=deadline,
            source_quote=content_text,
            confidence=self._confidence(
                actor=actor,
                action=action,
                obj=obj,
                deadline=deadline,
                modality=modality,
            ),
            slot_confidence=self._slot_confidence(
                actor=actor,
                action=action,
                obj=obj,
                domain=domain,
                deadline=deadline,
            ),
            metadata={"unit_type": unit.get("unit_type")},
        )
        return [assertion]

    def _segments(self, content_text: str) -> list[str]:
        segments = [
            item.strip()
            for item in re.split(r"(?<=[.!?])\s+", content_text)
            if len(item.strip()) >= 8
        ]
        return segments or [content_text]

    def _slot(self, match: OntologyMatch | None) -> LegalSlot | None:
        if match is None:
            return None
        return LegalSlot(
            raw=match.raw_label,
            canonical=match.canonical,
            confidence=match.confidence,
            metadata=match.metadata,
        )

    def _domain_slot(
        self, content_text: str, actor: LegalSlot | None, obj: LegalSlot | None
    ) -> LegalSlot | None:
        ontology = get_ontology_service()
        object_domains = ontology.object_domains(obj.canonical if obj else None)
        if object_domains:
            return LegalSlot(
                raw=object_domains[0],
                canonical=object_domains[0],
                confidence=0.82,
                metadata={"source": "object_domain"},
            )
        actor_domains = ontology.actor_domains(actor.canonical if actor else None)
        if actor_domains:
            return LegalSlot(
                raw=actor_domains[0],
                canonical=actor_domains[0],
                confidence=0.72,
                metadata={"source": "actor_domain"},
            )
        match = ontology.match_domain(content_text)
        return self._slot(match)

    def _deadline(self, content_text: str) -> DeadlineSlot | None:
        normalized = normalize_legal_text(content_text)
        match = _DEADLINE_RE.search(normalized)
        if match is None:
            return None
        raw_value = match.group("value")
        value = int(raw_value) if raw_value.isdigit() else _NUMBER_WORDS[raw_value]
        working = bool(match.group("working"))
        return DeadlineSlot(
            raw=match.group(0),
            value=value,
            unit="working_day" if working else "day",
            calendar_type="working_day" if working else "calendar_day",
            confidence=0.86,
        )

    def _modality(self, normalized_text: str) -> str | None:
        if _PROHIBITION_RE.search(normalized_text):
            return "must_not"
        if _AUTHORIZATION_RE.search(normalized_text):
            return "is_authorized"
        if _OBLIGATION_RE.search(normalized_text):
            return "must"
        if _PERMISSION_RE.search(normalized_text):
            return "may"
        if _COMPETENCE_RE.search(normalized_text):
            return "is_competent"
        return None

    def _assertion_type(
        self,
        *,
        normalized: str,
        modality: str | None,
        action: LegalSlot | None,
        deadline: DeadlineSlot | None,
    ) -> str | None:
        if _COMPETENCE_RE.search(normalized) or modality == "is_competent":
            return "competence"
        if deadline is not None:
            return "deadline"
        if modality == "must_not":
            return "prohibition"
        if modality == "must":
            return "obligation"
        if modality in {"may", "is_authorized"}:
            return "permission"
        if action is not None:
            return "norm"
        return None

    def _confidence(
        self,
        *,
        actor: LegalSlot | None,
        action: LegalSlot | None,
        obj: LegalSlot | None,
        deadline: DeadlineSlot | None,
        modality: str | None,
    ) -> float:
        score = 0.48
        if actor:
            score += 0.12
        if action:
            score += 0.12
        if obj:
            score += 0.10
        if deadline:
            score += 0.12
        if modality:
            score += 0.06
        return min(score, 0.94)

    def _slot_confidence(
        self,
        *,
        actor: LegalSlot | None,
        action: LegalSlot | None,
        obj: LegalSlot | None,
        domain: LegalSlot | None,
        deadline: DeadlineSlot | None,
    ) -> dict[str, float]:
        values = {}
        if actor:
            values["actor"] = actor.confidence
        if action:
            values["action"] = action.confidence
        if obj:
            values["object"] = obj.confidence
        if domain:
            values["domain"] = domain.confidence
        if deadline:
            values["deadline"] = deadline.confidence
        return values

    def _assertion_id(
        self,
        *,
        source_uri: str,
        legal_unit_id: str,
        assertion_type: str,
        source_quote: str,
    ) -> UUID:
        key = f"{source_uri}#{legal_unit_id}#{assertion_type}#{source_quote[:80]}"
        return uuid5(NAMESPACE_URL, key)


@lru_cache
def get_assertion_extraction_service() -> AssertionExtractionService:
    return AssertionExtractionService()
