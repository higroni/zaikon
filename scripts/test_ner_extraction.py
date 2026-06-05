"""Test NER extraction on sample legal text."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from zaikon.modules.ner.service import get_ner_service
from zaikon.modules.ontology.service import get_ontology_service

# Sample text from radni odnosi
sample_texts = [
    "Poslodavac je dužan da zaposlenom isplati zaradu.",
    "Zaposleni ima pravo na godišnji odmor.",
    "Ministarstvo vrši kontrolu primene zakona.",
    "Radnik podnosi zahtev za ostvarivanje prava.",
    "Poslodavac mora da vodi evidenciju o radnom vremenu.",
]

def test_extraction():
    print("=" * 60)
    print("NER EXTRACTION TEST")
    print("=" * 60)
    
    ner_service = get_ner_service()
    ontology = get_ontology_service()
    
    print(f"\nNER Enabled: {ner_service.is_enabled()}")
    print(f"Ontology loaded: {len(ontology.snapshot().actors)} actors, "
          f"{len(ontology.snapshot().actions)} actions, "
          f"{len(ontology.snapshot().objects)} objects")
    
    for i, text in enumerate(sample_texts, 1):
        print(f"\n{'=' * 60}")
        print(f"TEXT {i}: {text}")
        print(f"{'=' * 60}")
        
        # Test ontology
        print("\n--- ONTOLOGY MATCHING ---")
        actor_match = ontology.match_actor(text)
        action_match = ontology.match_action(text)
        object_match = ontology.match_object(text)
        
        print(f"Actor:  {actor_match.canonical if actor_match else 'NONE'}")
        print(f"Action: {action_match.canonical if action_match else 'NONE'}")
        print(f"Object: {object_match.canonical if object_match else 'NONE'}")
        
        # Test NER
        print("\n--- NER EXTRACTION ---")
        ner_result = ner_service.extract(text)
        
        print(f"Actors:  {len(ner_result.actors)}")
        for actor in ner_result.actors:
            print(f"  - {actor.text} ({actor.lemma}) [conf: {actor.confidence:.2f}]")
        
        print(f"Actions: {len(ner_result.actions)}")
        for action in ner_result.actions:
            print(f"  - {action.text} ({action.lemma}) [conf: {action.confidence:.2f}]")
        
        print(f"Objects: {len(ner_result.objects)}")
        for obj in ner_result.objects:
            print(f"  - {obj.text} ({obj.lemma}) [conf: {obj.confidence:.2f}]")

if __name__ == "__main__":
    test_extraction()

# Made with Bob
