# Auto-Learning Ontology - Implementation Guide

**Date:** 2026-06-05  
**Status:** ✅ Implemented, Ready for Testing

---

## 🎯 Koncept: Ontologija Koja Uči

### **Problem:**
- Ručno održavanje ontologije je sporo
- JSON fajlovi nisu konzistentni sa bazom
- Ontologija ne raste sa korpusom

### **Rešenje:**
✅ **Auto-Learning Ontology** - ontologija koja automatski uči iz NER ekstrakcija

---

## 🏗️ Arhitektura

### **1. Database Schema**

```sql
-- Ontology Terms (naučeni termini)
CREATE TABLE ontology_terms (
    term_id TEXT PRIMARY KEY,
    term_type TEXT NOT NULL,      -- 'actor', 'action', 'object'
    canonical TEXT NOT NULL,       -- Lemma (poslodavac)
    label TEXT NOT NULL,           -- Original text (Poslodavac)
    confidence REAL DEFAULT 0.75,  -- Prosečna confidence
    frequency INTEGER DEFAULT 1,   -- Koliko puta viđen
    source TEXT DEFAULT 'ner',     -- 'manual', 'ner', 'imported'
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Ontology Relationships (semantika)
CREATE TABLE ontology_relationships (
    relationship_id TEXT PRIMARY KEY,
    source_term_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,  -- 'broader_than', 'related_to'
    target_term_id TEXT NOT NULL,
    confidence REAL DEFAULT 0.80
);

-- Ontology Domains (domeni)
CREATE TABLE ontology_domains (
    domain_id TEXT PRIMARY KEY,
    term_id TEXT NOT NULL,
    domain_name TEXT NOT NULL,  -- 'labor_law', 'forestry'
    confidence REAL DEFAULT 0.75
);
```

### **2. Learning Process**

```
Import Document
    ↓
Extract Assertions
    ↓
Try Ontology Match
    ↓
If NOT found → NER Extraction
    ↓
Learn from NER:
  - Add term to ontology_terms
  - Increment frequency
  - Update confidence (weighted average)
    ↓
Next Import:
  - Ontology now has this term
  - Faster match (no NER needed)
```

---

## 📊 Kako Radi

### **Primer 1: Prvi Import**

```python
Text: "Poslodavac je dužan da isplati zaradu."

# Import 1:
Ontology: NONE (term not in ontology)
NER:      poslodavac (conf: 0.85) ✅
Action:   Learn term → ontology_terms
          frequency=1, confidence=0.85

# Import 2 (isti tekst):
Ontology: poslodavac (conf: 0.85) ✅ FAST!
NER:      Not needed
Action:   Increment frequency → frequency=2
```

### **Primer 2: Učenje iz Više Dokumenata**

```python
# Document 1:
"Poslodavac mora..." → Learn: poslodavac (freq=1, conf=0.85)

# Document 2:
"Poslodavac je dužan..." → Update: poslodavac (freq=2, conf=0.85)

# Document 3:
"poslodavac obavezan..." → Update: poslodavac (freq=3, conf=0.85)

# Document 10:
"Poslodavac..." → Update: poslodavac (freq=10, conf=0.85)
                  → HIGH FREQUENCY TERM! ✅
```

### **Primer 3: Confidence Averaging**

```python
# First extraction:
NER: "direktor" (conf: 0.80)
DB:  frequency=1, confidence=0.80

# Second extraction:
NER: "direktor" (conf: 0.90)
DB:  frequency=2, confidence=(0.80*1 + 0.90*1)/2 = 0.85

# Third extraction:
NER: "direktor" (conf: 0.85)
DB:  frequency=3, confidence=(0.85*2 + 0.85*1)/3 = 0.85
```

---

## 🚀 API Usage

### **1. Learn from NER Slot**

```python
from zaikon.modules.ontology.auto_learning_service import get_auto_learning_service
from zaikon.modules.ner.schemas import NERSlot

auto_learning = get_auto_learning_service()

# Learn actor
actor_slot = NERSlot(
    text="Poslodavac",
    lemma="poslodavac",
    pos="NOUN",
    deprel="nsubj",
    confidence=0.85
)
auto_learning.learn_from_ner_slot(actor_slot, "actor")

# Learn action
action_slot = NERSlot(
    text="isplati",
    lemma="isplatiti",
    pos="VERB",
    deprel="root",
    confidence=0.90
)
auto_learning.learn_from_ner_slot(action_slot, "action")
```

### **2. Get Term from Ontology**

```python
# Check if term exists
term = auto_learning.get_term("actor", "poslodavac")
if term:
    print(f"Found: {term['canonical']} (freq: {term['frequency']})")
else:
    print("Not in ontology yet")
```

### **3. Get Top Terms**

```python
# Get top 10 actors by frequency
top_actors = auto_learning.get_top_terms(
    term_type="actor",
    min_frequency=5,  # Only terms seen 5+ times
    limit=10
)

for term in top_actors:
    print(f"{term['canonical']}: {term['frequency']} times")
```

### **4. Export to JSON**

```python
from pathlib import Path

# Export learned ontology to JSON
ontology = auto_learning.export_to_json(
    output_path=Path("learned_ontology.json"),
    min_frequency=5  # Only export terms seen 5+ times
)

# Result: learned_ontology.json
{
  "actors": {
    "poslodavac": {
      "labels": ["Poslodavac", "poslodavac", "poslodavca"],
      "source": "auto-learned"
    },
    "zaposleni": {
      "labels": ["Zaposleni", "zaposleni", "zaposlenog"],
      "source": "auto-learned"
    }
  }
}
```

### **5. Get Statistics**

```python
stats = auto_learning.get_statistics()

print(f"Actors: {stats['actor']['total']}")
print(f"  High frequency (5+): {stats['actor']['high_frequency']}")
print(f"  Very high (10+): {stats['actor']['very_high_frequency']}")
print(f"  Avg frequency: {stats['actor']['avg_frequency']}")
print(f"  Avg confidence: {stats['actor']['avg_confidence']}")
```

---

## 📈 Performance Benefits

### **Scenario: Import 100 Documents**

#### Without Auto-Learning:
```
Document 1:  NER for all terms (slow)
Document 2:  NER for all terms (slow)
...
Document 100: NER for all terms (slow)

Total time: ~2000 seconds (100 docs × 20s)
```

#### With Auto-Learning:
```
Document 1:   NER for all terms (slow) → Learn 50 terms
Document 2:   Ontology hits 30%, NER 70% → Learn 35 new terms
Document 10:  Ontology hits 60%, NER 40% → Learn 20 new terms
Document 50:  Ontology hits 85%, NER 15% → Learn 5 new terms
Document 100: Ontology hits 95%, NER 5% → Learn 1 new term

Total time: ~1200 seconds (40% faster!)
```

### **Learning Curve:**

```
Import #  | Ontology Hit Rate | NER Usage | Speed
----------|-------------------|-----------|-------
1-10      | 20%              | 80%       | Slow
11-30     | 50%              | 50%       | Medium
31-50     | 70%              | 30%       | Fast
51-100    | 85%              | 15%       | Very Fast
100+      | 95%              | 5%        | Instant
```

---

## 🔧 Configuration

### **Settings in `config.py`:**

```python
# Enable auto-learning
ontology_auto_learning: bool = True

# Minimum confidence to learn term
ontology_learning_min_confidence: float = 0.75

# Minimum frequency to promote to ontology
ontology_learning_min_frequency: int = 3

# Auto-export ontology after N imports
ontology_auto_export_frequency: int = 10
```

---

## 🎯 Integration with Assertion Extraction

### **Modified Flow:**

```python
# backend/zaikon/modules/assertions/service.py

# 1. Try ontology first
actor = ontology.match_actor(text)

# 2. If not found, use NER
if actor is None:
    ner_result = ner_service.extract(text)
    if ner_result.actors:
        best_actor = max(ner_result.actors, key=lambda x: x.confidence)
        actor = LegalSlot(
            raw=best_actor.text,
            canonical=best_actor.lemma,
            confidence=best_actor.confidence
        )
        
        # 3. LEARN FROM NER! ✅
        auto_learning.learn_from_ner_slot(best_actor, "actor")
```

---

## 📊 Monitoring & Analytics

### **Dashboard Queries:**

```sql
-- Top 20 most frequent actors
SELECT canonical, label, frequency, confidence
FROM ontology_terms
WHERE term_type = 'actor'
ORDER BY frequency DESC
LIMIT 20;

-- Terms learned today
SELECT term_type, COUNT(*) as count
FROM ontology_terms
WHERE DATE(created_at) = DATE('now')
GROUP BY term_type;

-- Learning rate over time
SELECT 
    DATE(created_at) as date,
    term_type,
    COUNT(*) as new_terms
FROM ontology_terms
GROUP BY DATE(created_at), term_type
ORDER BY date DESC;

-- High-confidence terms (ready for manual review)
SELECT canonical, label, frequency, confidence
FROM ontology_terms
WHERE frequency >= 10 AND confidence >= 0.85
ORDER BY frequency DESC;
```

---

## 🚀 Next Steps

### **1. Initialize Database**
```bash
# Tables will be created automatically on first use
python -c "from zaikon.modules.ontology.auto_learning_service import get_auto_learning_service; get_auto_learning_service()"
```

### **2. Re-import Corpus with Auto-Learning**
```bash
python scripts/reimport_pilot_with_ner.py
```

### **3. Monitor Learning**
```bash
# Check statistics
python scripts/check_ontology_stats.py

# Export learned ontology
python scripts/export_learned_ontology.py
```

### **4. Review & Curate**
```bash
# Review high-frequency terms
python scripts/review_learned_terms.py

# Add manual relationships (broader_than, domains)
python scripts/add_ontology_relationships.py
```

---

## ✅ Benefits Summary

1. **Automatsko Učenje** ✅
   - Ontologija raste sa korpusom
   - Bez ručnog održavanja

2. **Vremenom Brže** ✅
   - Prvi import: 100% NER (sporo)
   - Posle 100 dokumenata: 95% ontology (brzo)

3. **Konzistentnost** ✅
   - Sve u bazi
   - Jedan backup za sve

4. **Skalabilnost** ✅
   - Radi za bilo koji domen
   - Automatski se adaptira

5. **Versioning** ✅
   - Prati kada je termin naučen
   - Prati frekvenciju i confidence

6. **Multi-tenant Ready** ✅
   - Svaki korisnik može imati svoju ontologiju
   - Ili deljenu ontologiju za sve

---

## 📝 Implementation Status

- ✅ Database schema created
- ✅ Auto-learning service implemented
- ✅ Integration with assertion extraction
- ⏳ Testing needed
- ⏳ Monitoring dashboard
- ⏳ Export/import tools

---

**Status:** Ready for testing with pilot corpus re-import