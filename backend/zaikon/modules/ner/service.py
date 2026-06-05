"""Stanza-based NER service for Serbian legal text."""

import logging
from functools import lru_cache
from typing import Any

from zaikon.core.config import settings
from zaikon.modules.ner.schemas import NERExtraction, NERSlot

logger = logging.getLogger(__name__)


class StanzaNERService:
    """Named Entity Recognition service using Stanza for Serbian."""
    
    def __init__(self) -> None:
        self._nlp = None
        self._enabled = getattr(settings, 'ner_enabled', True)
        
    def _ensure_pipeline(self):
        """Lazy load Stanza pipeline."""
        if self._nlp is not None:
            return
            
        if not self._enabled:
            logger.info("NER is disabled, skipping Stanza initialization")
            return
            
        try:
            import torch
            import stanza
            logger.info("Initializing Stanza pipeline for Serbian...")
            
            # Patch torch.load to use weights_only=False for Stanza compatibility
            # Stanza models use pickle protocol 3 which requires this
            original_load = torch.load
            def patched_load(*args, **kwargs):
                kwargs['weights_only'] = False
                return original_load(*args, **kwargs)
            torch.load = patched_load
            
            # Download Serbian model if not present
            try:
                stanza.download('sr', verbose=False)
            except Exception as e:
                logger.warning(f"Could not download Stanza model: {e}")
            
            # Initialize pipeline with required processors
            self._nlp = stanza.Pipeline(
                'sr',
                processors='tokenize,pos,lemma,depparse',
                verbose=False,
                use_gpu=False,  # Use CPU for stability
                download_method=None,  # Don't auto-download
            )
            
            # Restore original torch.load
            torch.load = original_load
            
            logger.info("Stanza pipeline initialized successfully")
            
        except ImportError:
            logger.warning("Stanza not installed, NER extraction will be disabled")
            self._enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Stanza: {e}")
            self._enabled = False
    
    def extract(self, text: str) -> NERExtraction:
        """Extract actors, actions, and objects from text using NER.
        
        Args:
            text: The text to analyze
            
        Returns:
            NERExtraction with extracted slots
        """
        if not self._enabled:
            return NERExtraction()
            
        self._ensure_pipeline()
        
        if self._nlp is None:
            return NERExtraction()
        
        try:
            # Analyze text
            logger.debug(f"Analyzing text: {text[:100]}...")
            doc = self._nlp(text)
            logger.debug(f"Parsed {len(doc.sentences)} sentences")
            
            actors = []
            actions = []
            objects = []
            
            # Extract from each sentence
            for sent in doc.sentences:
                logger.debug(f"Sentence has {len(sent.words)} words")
                for word in sent.words:
                    logger.debug(f"Word: {word.text}, POS: {word.upos}, Deprel: {word.deprel}")
                    # Actor: nouns or adjectives that are subjects
                    # (Serbian adjectives can function as nouns, e.g., "zaposleni")
                    if word.upos in ["NOUN", "ADJ"] and word.deprel in ["nsubj", "nsubj:pass"]:
                        actors.append(NERSlot(
                            text=word.text,
                            lemma=word.lemma,
                            pos=word.upos,
                            deprel=word.deprel,
                            confidence=0.85 if word.upos == "NOUN" else 0.75
                        ))
                    
                    # Action: verbs (main predicates)
                    elif word.upos == "VERB" and word.deprel in ["root", "xcomp", "ccomp"]:
                        actions.append(NERSlot(
                            text=word.text,
                            lemma=word.lemma,
                            pos=word.upos,
                            deprel=word.deprel,
                            confidence=0.90
                        ))
                    
                    # Object: nouns that are objects or oblique arguments
                    elif word.upos == "NOUN" and word.deprel in ["obj", "iobj", "obl"]:
                        objects.append(NERSlot(
                            text=word.text,
                            lemma=word.lemma,
                            pos=word.upos,
                            deprel=word.deprel,
                            confidence=0.80
                        ))
            
            return NERExtraction(
                actors=actors,
                actions=actions,
                objects=objects,
                metadata={
                    "sentence_count": len(doc.sentences),
                    "word_count": sum(len(sent.words) for sent in doc.sentences)
                }
            )
            
        except Exception as e:
            logger.error(f"NER extraction failed: {e}")
            return NERExtraction()
    
    def is_enabled(self) -> bool:
        """Check if NER is enabled and available."""
        return self._enabled


@lru_cache
def get_ner_service() -> StanzaNERService:
    """Get singleton NER service instance."""
    return StanzaNERService()

# Made with Bob
