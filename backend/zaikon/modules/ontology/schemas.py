"""Ontology module schemas."""

from typing import Any

from pydantic import BaseModel, Field


class OntologyMatch(BaseModel):
    term_type: str
    canonical: str
    raw_label: str
    confidence: float = 0.8
    metadata: dict[str, Any] = Field(default_factory=dict)


class OntologySnapshot(BaseModel):
    version: str
    language: str = "sr"
    actors: dict[str, dict[str, Any]] = Field(default_factory=dict)
    actions: dict[str, dict[str, Any]] = Field(default_factory=dict)
    objects: dict[str, dict[str, Any]] = Field(default_factory=dict)
    domains: dict[str, dict[str, Any]] = Field(default_factory=dict)


class OntologyResponse(BaseModel):
    ontology: OntologySnapshot
