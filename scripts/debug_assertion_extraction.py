"""Debug assertion extraction with NER fallback."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from zaikon.core.config import settings
from zaikon.modules.assertions.service import AssertionExtractionService
from zaikon.modules.canonical.schemas import CanonicalDocument

# Sample canonical document
sample_doc = CanonicalDocument(
    source_uri="test://debug",
    filename="debug.txt",
    document_type="law",
    canonical_json={
        "legal_units": [
            {
                "legal_unit_id": "test-001",
                "path": "test/001",
                "unit_type": "article",
                "content_text": "Poslodavac je dužan da zaposlenom isplati zaradu."
            }
        ]
    }
)

def debug_extraction():
    print("=" * 60)
    print("ASSERTION EXTRACTION DEBUG")
    print("=" * 60)
    
    print(f"\nSettings:")
    print(f"  ner_enabled: {settings.ner_enabled}")
    print(f"  ner_fallback_to_ontology: {settings.ner_fallback_to_ontology}")
    
    service = AssertionExtractionService()
    
    print(f"\nExtracting from: '{sample_doc.canonical_json['legal_units'][0]['content_text']}'")
    
    assertions = service.extract_from_document(
        document=sample_doc,
        corpus_id=None,
        pipeline_run_id=None,
        document_id="test-doc"
    )
    
    print(f"\nExtracted {len(assertions)} assertions:")
    for i, assertion in enumerate(assertions, 1):
        print(f"\n--- Assertion {i} ---")
        print(f"Type: {assertion.assertion_type}")
        print(f"Modality: {assertion.modality}")
        print(f"Actor: {assertion.actor}")
        print(f"Action: {assertion.action}")
        print(f"Object: {assertion.object}")
        print(f"Confidence: {assertion.confidence:.2f}")
        print(f"Source: {assertion.source_quote}")

if __name__ == "__main__":
    debug_extraction()

# Made with Bob
