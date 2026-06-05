"""Check auto-learning ontology statistics."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from zaikon.modules.ontology.auto_learning_service import get_auto_learning_service


def main():
    print("=" * 60)
    print("AUTO-LEARNING ONTOLOGY STATISTICS")
    print("=" * 60)
    
    auto_learning = get_auto_learning_service()
    stats = auto_learning.get_statistics()
    
    print("\n📊 OVERALL STATISTICS:")
    print("-" * 60)
    
    for term_type in ["actor", "action", "object"]:
        s = stats[term_type]
        print(f"\n{term_type.upper()}S:")
        print(f"  Total terms:           {s['total']}")
        print(f"  High frequency (5+):   {s['high_frequency']}")
        print(f"  Very high freq (10+):  {s['very_high_frequency']}")
        print(f"  Average frequency:     {s['avg_frequency']:.2f}")
        print(f"  Average confidence:    {s['avg_confidence']:.2f}")
    
    print("\n" + "=" * 60)
    print("TOP TERMS BY FREQUENCY")
    print("=" * 60)
    
    for term_type in ["actor", "action", "object"]:
        print(f"\n{term_type.upper()}S (top 10):")
        print("-" * 60)
        
        top_terms = auto_learning.get_top_terms(
            term_type=term_type,
            min_frequency=1,
            limit=10
        )
        
        if not top_terms:
            print("  (no terms learned yet)")
            continue
        
        for i, term in enumerate(top_terms, 1):
            print(f"  {i:2d}. {term['canonical']:20s} "
                  f"(freq: {term['frequency']:3d}, "
                  f"conf: {term['confidence']:.2f}, "
                  f"source: {term['source']})")


if __name__ == "__main__":
    main()

# Made with Bob
