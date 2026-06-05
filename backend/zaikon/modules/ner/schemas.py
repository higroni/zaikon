"""Schemas for NER extraction results."""

from pydantic import BaseModel, Field


class NERSlot(BaseModel):
    """A slot extracted by NER."""
    
    text: str = Field(description="The extracted text")
    lemma: str = Field(description="Lemmatized form")
    pos: str = Field(description="Part of speech tag (NOUN, VERB, etc.)")
    deprel: str | None = Field(default=None, description="Dependency relation (nsubj, obj, etc.)")
    confidence: float = Field(default=0.8, description="Confidence score")


class NERExtraction(BaseModel):
    """Result of NER extraction from text."""
    
    actors: list[NERSlot] = Field(default_factory=list, description="Extracted actors (subjects)")
    actions: list[NERSlot] = Field(default_factory=list, description="Extracted actions (verbs)")
    objects: list[NERSlot] = Field(default_factory=list, description="Extracted objects")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

# Made with Bob
