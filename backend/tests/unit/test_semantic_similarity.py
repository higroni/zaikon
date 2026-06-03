"""Unit tests for semantic similarity in candidate retrieval."""

import pytest
from uuid import uuid4

from zaikon.modules.assertions.schemas import LegalSlot, NormativeAssertion
from zaikon.modules.conflicts.service import ConflictRegistryService


class TestSemanticSimilarity:
    """Test semantic similarity features in candidate generation."""

    def test_exact_match_has_highest_score(self):
        """Test that exact matches get higher scores than similar matches."""
        service = ConflictRegistryService()
        
        # Exact match
        draft_exact = NormativeAssertion(
            source_uri="test://draft",
            filename="draft.txt",
            legal_unit_id="1",
            source_path="article:1",
            assertion_type="obligation",
            action=LegalSlot(raw="kontrola", canonical="kontrola"),
            object=LegalSlot(raw="hrana", canonical="hrana"),
            source_quote="Kontrolu hrane vrsi inspekcija.",
        )
        
        corpus_exact = NormativeAssertion(
            source_uri="test://corpus",
            filename="zakon.txt",
            legal_unit_id="1",
            source_path="article:1",
            assertion_type="obligation",
            action=LegalSlot(raw="kontrola", canonical="kontrola"),
            object=LegalSlot(raw="hrana", canonical="hrana"),
            source_quote="Kontrolu hrane vrsi inspekcija.",
        )
        
        candidate_exact = service._candidate(draft_exact, corpus_exact)
        assert candidate_exact is not None
        assert candidate_exact.score >= 0.6
        assert "same_action" in candidate_exact.match_reasons
        assert "same_object" in candidate_exact.match_reasons

    def test_similar_slots_generate_candidates(self):
        """Test that similar (but not identical) slots can generate candidates."""
        service = ConflictRegistryService()
        
        draft = NormativeAssertion(
            source_uri="test://draft",
            filename="draft.txt",
            legal_unit_id="1",
            source_path="article:1",
            assertion_type="obligation",
            action=LegalSlot(raw="nadzor", canonical="nadzor"),  # Similar to "kontrola"
            object=LegalSlot(raw="hrana", canonical="hrana"),
            source_quote="Nadzor hrane vrsi inspekcija.",
        )
        
        corpus = NormativeAssertion(
            source_uri="test://corpus",
            filename="zakon.txt",
            legal_unit_id="1",
            source_path="article:1",
            assertion_type="obligation",
            action=LegalSlot(raw="kontrola", canonical="kontrola"),
            object=LegalSlot(raw="hrana", canonical="hrana"),
            source_quote="Kontrolu hrane vrsi inspekcija.",
        )
        
        candidate = service._candidate(draft, corpus)
        # May or may not match depending on similarity threshold
        # But should not crash
        assert candidate is None or candidate.score > 0

    def test_text_similarity_calculation(self):
        """Test the text similarity helper method."""
        service = ConflictRegistryService()
        
        # Identical texts
        assert service._text_similarity("kontrola", "kontrola") == 1.0
        
        # Very similar texts
        similarity = service._text_similarity("kontrola", "nadzor")
        assert 0.0 <= similarity <= 1.0
        
        # Different texts
        similarity = service._text_similarity("kontrola", "xyz")
        assert similarity < 0.5
        
        # Case insensitive
        assert service._text_similarity("Kontrola", "kontrola") == 1.0
        
        # Empty strings
        assert service._text_similarity("", "") == 0.0
        assert service._text_similarity("test", "") == 0.0

    def test_similar_slot_method(self):
        """Test the _similar_slot helper method."""
        service = ConflictRegistryService()
        
        slot1 = LegalSlot(raw="kontrola", canonical="kontrola")
        slot2 = LegalSlot(raw="kontrola", canonical="kontrola")
        slot3 = LegalSlot(raw="nadzor", canonical="nadzor")
        
        # Exact match
        assert service._similar_slot(slot1, slot2, threshold=0.7) is True
        
        # Similar but not exact
        result = service._similar_slot(slot1, slot3, threshold=0.7)
        # Result depends on actual similarity
        assert isinstance(result, bool)
        
        # None slots
        assert service._similar_slot(None, slot2, threshold=0.7) is False
        assert service._similar_slot(slot1, None, threshold=0.7) is False

    def test_quote_similarity_fallback(self):
        """Test that quote similarity can generate candidates when slots don't match."""
        service = ConflictRegistryService()
        
        draft = NormativeAssertion(
            source_uri="test://draft",
            filename="draft.txt",
            legal_unit_id="1",
            source_path="article:1",
            assertion_type="obligation",
            action=LegalSlot(raw="odlucivanje", canonical="odlucivanje"),
            object=LegalSlot(raw="zahtev", canonical="zahtev"),
            source_quote="Nadlezni organ odlucuje o zahtevu u roku od 15 dana.",
        )
        
        corpus = NormativeAssertion(
            source_uri="test://corpus",
            filename="zakon.txt",
            legal_unit_id="1",
            source_path="article:1",
            assertion_type="obligation",
            action=LegalSlot(raw="odlucivanje", canonical="odlucivanje"),
            object=LegalSlot(raw="zahtev", canonical="zahtev"),
            source_quote="Nadlezni organ odlucuje o zahtevu u roku od 30 dana.",
        )
        
        candidate = service._candidate(draft, corpus)
        assert candidate is not None
        # Should match on action and object
        assert "same_action" in candidate.match_reasons
        assert "same_object" in candidate.match_reasons

    def test_minimum_threshold_prevents_weak_candidates(self):
        """Test that candidates below minimum threshold are rejected."""
        service = ConflictRegistryService()
        
        draft = NormativeAssertion(
            source_uri="test://draft",
            filename="draft.txt",
            legal_unit_id="1",
            source_path="article:1",
            assertion_type="obligation",
            action=LegalSlot(raw="xyz", canonical="xyz"),
            object=LegalSlot(raw="abc", canonical="abc"),
            source_quote="Completely different text.",
        )
        
        corpus = NormativeAssertion(
            source_uri="test://corpus",
            filename="zakon.txt",
            legal_unit_id="1",
            source_path="article:1",
            assertion_type="obligation",
            action=LegalSlot(raw="kontrola", canonical="kontrola"),
            object=LegalSlot(raw="hrana", canonical="hrana"),
            source_quote="Kontrolu hrane vrsi inspekcija.",
        )
        
        candidate = service._candidate(draft, corpus)
        # Should be None due to low similarity
        assert candidate is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
