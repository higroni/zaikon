"""Detailed analysis of assertions in database."""
import sqlite3
import json
from pathlib import Path
from collections import Counter

def analyze_assertions():
    """Analyze assertions in detail."""
    db_path = Path("data/zaikon.db")
    
    if not db_path.exists():
        print("❌ Database not found!")
        return
    
    print("=" * 60)
    print("DETAILED ASSERTION ANALYSIS")
    print("=" * 60)
    print()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all assertions
    cursor.execute("SELECT assertion_json FROM corpus_assertions")
    rows = cursor.fetchall()
    
    print(f"Total assertions: {len(rows)}")
    print()
    
    # Analyze slot coverage
    has_actor = 0
    has_action = 0
    has_object = 0
    has_all_three = 0
    
    actor_sources = Counter()
    action_sources = Counter()
    object_sources = Counter()
    
    sample_with_all = []
    sample_ner_based = []
    
    for row in rows:
        assertion = json.loads(row[0])
        
        actor = assertion.get('actor')
        action = assertion.get('action')
        obj = assertion.get('object')
        
        # Count coverage
        if actor and actor.get('canonical'):
            has_actor += 1
            conf = actor.get('confidence', 0)
            if conf > 0.9:
                actor_sources['ontology'] += 1
            else:
                actor_sources['ner'] += 1
        
        if action and action.get('canonical'):
            has_action += 1
            conf = action.get('confidence', 0)
            if conf > 0.9:
                action_sources['ontology'] += 1
            else:
                action_sources['ner'] += 1
        
        if obj and obj.get('canonical'):
            has_object += 1
            conf = obj.get('confidence', 0)
            if conf > 0.9:
                object_sources['ontology'] += 1
            else:
                object_sources['ner'] += 1
        
        if (actor and actor.get('canonical') and 
            action and action.get('canonical') and 
            obj and obj.get('canonical')):
            has_all_three += 1
            if len(sample_with_all) < 5:
                sample_with_all.append(assertion)
        
        # Check if any slot is NER-based
        is_ner = False
        if actor and actor.get('confidence', 1.0) < 0.9:
            is_ner = True
        if action and action.get('confidence', 1.0) < 0.9:
            is_ner = True
        if obj and obj.get('confidence', 1.0) < 0.9:
            is_ner = True
        
        if is_ner and len(sample_ner_based) < 10:
            sample_ner_based.append(assertion)
    
    # Print statistics
    print("SLOT COVERAGE:")
    print(f"  Assertions with Actor:  {has_actor:4d} ({has_actor/len(rows)*100:5.1f}%)")
    print(f"  Assertions with Action: {has_action:4d} ({has_action/len(rows)*100:5.1f}%)")
    print(f"  Assertions with Object: {has_object:4d} ({has_object/len(rows)*100:5.1f}%)")
    print(f"  Assertions with ALL 3:  {has_all_three:4d} ({has_all_three/len(rows)*100:5.1f}%)")
    print()
    
    print("EXTRACTION SOURCE:")
    print(f"  Actor  - Ontology: {actor_sources['ontology']:4d}, NER: {actor_sources['ner']:4d}")
    print(f"  Action - Ontology: {action_sources['ontology']:4d}, NER: {action_sources['ner']:4d}")
    print(f"  Object - Ontology: {object_sources['ontology']:4d}, NER: {object_sources['ner']:4d}")
    print()
    
    # Show samples with all three slots
    if sample_with_all:
        print("SAMPLE ASSERTIONS WITH ALL 3 SLOTS:")
        for i, assertion in enumerate(sample_with_all[:3], 1):
            actor = assertion.get('actor', {})
            action = assertion.get('action', {})
            obj = assertion.get('object', {})
            
            print(f"\n  [{i}] {assertion.get('assertion_type', 'unknown')}")
            print(f"      Actor:  {actor.get('canonical', 'N/A'):20s} (conf: {actor.get('confidence', 0):.2f})")
            print(f"      Action: {action.get('canonical', 'N/A'):20s} (conf: {action.get('confidence', 0):.2f})")
            print(f"      Object: {obj.get('canonical', 'N/A'):20s} (conf: {obj.get('confidence', 0):.2f})")
            print(f"      Quote:  {assertion.get('source_quote', '')[:60]}...")
    
    # Show NER-based samples
    if sample_ner_based:
        print("\n\nSAMPLE NER-BASED ASSERTIONS:")
        for i, assertion in enumerate(sample_ner_based[:5], 1):
            actor = assertion.get('actor', {})
            action = assertion.get('action', {})
            obj = assertion.get('object', {})
            
            print(f"\n  [{i}] {assertion.get('assertion_type', 'unknown')}")
            if actor and actor.get('canonical'):
                conf = actor.get('confidence', 0)
                source = "NER" if conf < 0.9 else "Ont"
                print(f"      Actor:  {actor.get('canonical', 'N/A'):20s} (conf: {conf:.2f}, {source})")
            if action and action.get('canonical'):
                conf = action.get('confidence', 0)
                source = "NER" if conf < 0.9 else "Ont"
                print(f"      Action: {action.get('canonical', 'N/A'):20s} (conf: {conf:.2f}, {source})")
            if obj and obj.get('canonical'):
                conf = obj.get('confidence', 0)
                source = "NER" if conf < 0.9 else "Ont"
                print(f"      Object: {obj.get('canonical', 'N/A'):20s} (conf: {conf:.2f}, {source})")
            print(f"      Quote:  {assertion.get('source_quote', '')[:60]}...")
    
    conn.close()
    print()
    print("=" * 60)

if __name__ == "__main__":
    analyze_assertions()

# Made with Bob
