"""Deterministic lightweight embeddings used as an offline fallback."""

from math import sqrt
import re
import unicodedata

_LATIN_FOLD = str.maketrans(
    {
        "č": "c",
        "ć": "c",
        "š": "s",
        "đ": "dj",
        "ž": "z",
        "Č": "c",
        "Ć": "c",
        "Š": "s",
        "Đ": "dj",
        "Ž": "z",
    }
)
_SYNONYMS = {
    "gazdovanje": {"upravljanje", "koriscenje", "odrzavanje"},
    "upravljanje": {"gazdovanje"},
    "sume": {"sumama", "suma", "sumarstvo"},
    "sumama": {"sume", "suma", "sumarstvo"},
    "evidencija": {"registar", "upisnik"},
    "registar": {"evidencija"},
}


def normalize_token(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).translate(_LATIN_FOLD).lower()
    return re.sub(r"[^a-z0-9]+", "", normalized)


def tokens(value: str) -> list[str]:
    base_tokens = [
        token
        for token in (normalize_token(item) for item in re.findall(r"\w+", value))
        if len(token) >= 3
    ]
    expanded = list(base_tokens)
    for token in base_tokens:
        expanded.extend(sorted(_SYNONYMS.get(token, set())))
    return expanded


def deterministic_embedding(value: str, dimensions: int = 64) -> list[float]:
    vector = [0.0] * dimensions
    for token in tokens(value):
        bucket = sum(ord(char) for char in token) % dimensions
        vector[bucket] += 1.0
    magnitude = sqrt(sum(item * item for item in vector))
    if not magnitude:
        return vector
    return [item / magnitude for item in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))
