"""Config-driven Serbian legal ontology."""

from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Any

from zaikon.core.config import settings
from zaikon.modules.ontology.schemas import OntologyMatch, OntologySnapshot


_FOLD_MAP = str.maketrans(
    {
        "\u010d": "c",
        "\u0107": "c",
        "\u0161": "s",
        "\u0111": "dj",
        "\u017e": "z",
        "\u010c": "c",
        "\u0106": "c",
        "\u0160": "s",
        "\u0110": "dj",
        "\u017d": "z",
        "\u0430": "a",
        "\u0431": "b",
        "\u0432": "v",
        "\u0433": "g",
        "\u0434": "d",
        "\u0452": "dj",
        "\u0435": "e",
        "\u0436": "z",
        "\u0437": "z",
        "\u0438": "i",
        "\u0458": "j",
        "\u043a": "k",
        "\u043b": "l",
        "\u0459": "lj",
        "\u043c": "m",
        "\u043d": "n",
        "\u045a": "nj",
        "\u043e": "o",
        "\u043f": "p",
        "\u0440": "r",
        "\u0441": "s",
        "\u0442": "t",
        "\u045b": "c",
        "\u0443": "u",
        "\u0444": "f",
        "\u0445": "h",
        "\u0446": "c",
        "\u0447": "c",
        "\u045f": "dz",
        "\u0448": "s",
        "\u0410": "a",
        "\u0411": "b",
        "\u0412": "v",
        "\u0413": "g",
        "\u0414": "d",
        "\u0402": "dj",
        "\u0415": "e",
        "\u0416": "z",
        "\u0417": "z",
        "\u0418": "i",
        "\u0408": "j",
        "\u041a": "k",
        "\u041b": "l",
        "\u0409": "lj",
        "\u041c": "m",
        "\u041d": "n",
        "\u040a": "nj",
        "\u041e": "o",
        "\u041f": "p",
        "\u0420": "r",
        "\u0421": "s",
        "\u0422": "t",
        "\u040b": "c",
        "\u0423": "u",
        "\u0424": "f",
        "\u0425": "h",
        "\u0426": "c",
        "\u0427": "c",
        "\u040f": "dz",
        "\u0428": "s",
    }
)


def normalize_legal_text(value: str) -> str:
    folded = value.translate(_FOLD_MAP).lower()
    return re.sub(r"\s+", " ", folded).strip()


class OntologyService:
    """Loads and queries legal ontology packs from JSON files."""

    def __init__(self, rules_dir: Path | None = None) -> None:
        self.rules_dir = rules_dir or (
            settings.base_dir / "backend" / "zaikon" / "rules" / "ontology"
        )
        self._snapshot = self._load_snapshot()

    def snapshot(self) -> OntologySnapshot:
        return self._snapshot

    def reload(self) -> OntologySnapshot:
        self._snapshot = self._load_snapshot()
        return self._snapshot

    def match_actor(self, text: str) -> OntologyMatch | None:
        return self._match("actors", text)

    def match_action(self, text: str) -> OntologyMatch | None:
        return self._match("actions", text)

    def match_object(self, text: str) -> OntologyMatch | None:
        return self._match("objects", text)

    def match_domain(self, text: str) -> OntologyMatch | None:
        return self._match("domains", text)

    def actor_domains(self, actor: str | None) -> list[str]:
        if not actor:
            return []
        record = self._snapshot.actors.get(actor, {})
        return list(record.get("domains", []))

    def object_domains(self, object_name: str | None) -> list[str]:
        if not object_name:
            return []
        record = self._snapshot.objects.get(object_name, {})
        return list(record.get("domains", []))

    def is_broader_actor(self, draft_actor: str | None, corpus_actor: str | None) -> bool:
        if not draft_actor or not corpus_actor or draft_actor == corpus_actor:
            return False
        seen = set()
        stack = [draft_actor]
        while stack:
            actor = stack.pop()
            if actor in seen:
                continue
            seen.add(actor)
            broader_than = self._snapshot.actors.get(actor, {}).get("broader_than", [])
            if corpus_actor in broader_than:
                return True
            stack.extend(item for item in broader_than if isinstance(item, str))
        return False

    def is_wrong_domain_for_object(
        self, *, actor: str | None, object_name: str | None
    ) -> bool:
        actor_domains = set(self.actor_domains(actor))
        object_domains = set(self.object_domains(object_name))
        return bool(actor_domains and object_domains and not actor_domains & object_domains)

    def _match(self, group_name: str, text: str) -> OntologyMatch | None:
        normalized_text = normalize_legal_text(text)
        group = getattr(self._snapshot, group_name)
        best: OntologyMatch | None = None
        for canonical, record in group.items():
            for label in record.get("labels", []):
                normalized_label = normalize_legal_text(str(label))
                if not normalized_label or normalized_label not in normalized_text:
                    continue
                confidence = min(0.99, 0.72 + len(normalized_label) / 100)
                candidate = OntologyMatch(
                    term_type=group_name.removesuffix("s"),
                    canonical=canonical,
                    raw_label=str(label),
                    confidence=confidence,
                    metadata={
                        key: value
                        for key, value in record.items()
                        if key not in {"labels"}
                    },
                )
                if best is None or candidate.confidence > best.confidence:
                    best = candidate
        return best

    def _load_snapshot(self) -> OntologySnapshot:
        payload: dict[str, Any] = {
            "version": "0.1.0",
            "language": "sr",
            "actors": {},
            "actions": {},
            "objects": {},
            "domains": {},
        }
        for path in sorted(self.rules_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            payload["version"] = str(data.get("version", payload["version"]))
            payload["language"] = str(data.get("language", payload["language"]))
            for group_name in ("actors", "actions", "objects", "domains"):
                payload[group_name].update(data.get(group_name, {}))
        return OntologySnapshot.model_validate(payload)


@lru_cache
def get_ontology_service() -> OntologyService:
    return OntologyService()
