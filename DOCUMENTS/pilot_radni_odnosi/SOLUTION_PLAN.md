# Plan za rešenje Conflict Detection problema

## Root Cause
Ontologija (`base_sr.json`) sadrži termine za šumarstvo/građevinu, ali pilot corpus je o **radnim odnosima**.

### Trenutna ontologija:
- **Actors:** 7 termina (ministarstva, građani, ovlašćena lica)
- **Actions:** 5 termina (kontroliše, obeležava drveće, donosi rešenje)
- **Objects:** 6 termina (hrana, drvo, šuma, zahtev)

### Pilot corpus termini (radni odnosi):
- **Actors:** zaposleni, poslodavac, sindikat, inspekcija rada, ministarstvo rada
- **Actions:** zaključuje ugovor, obaveštava, podnosi zahtev, isplaćuje zaradu, otkazuje ugovor
- **Objects:** ugovor o radu, zarada, minimalac, radni odnos, godišnji odmor, bolovanje

**Rezultat:** `_match()` ne pronalazi termine → vraća `None` → assertions nemaju action/object/actor

## Rešenje: 3 pristupa

### Pristup 1: Proširiti ontologiju (BRZO, ali ograničeno)
**Vreme:** 30-60 min  
**Kvalitet:** Srednji (pokriva osnovne termine)

1. Kreirati `labor_relations_sr.json` sa terminima za radne odnose
2. Dodati ~50-100 najčešćih termina iz pilot corpusa
3. Re-ekstraktovati assertions
4. Testirati conflict detection

**Prednosti:**
- ✅ Brzo rešenje
- ✅ Koristi postojeću infrastrukturu
- ✅ Lako održavanje

**Mane:**
- ❌ Ručno dodavanje termina
- ❌ Pokriva samo poznate termine
- ❌ Ne skalira dobro

### Pristup 2: NER model (SREDNJE, bolji kvalitet)
**Vreme:** 2-4 sata  
**Kvalitet:** Dobar (automatski ekstrahuje termine)

1. Koristiti spaCy ili Stanza za srpski
2. Trenirati/fine-tune-ovati na pravnim tekstovima
3. Ekstraktovati entitete (PERSON, ORG, ACTION, OBJECT)
4. Mapirati na ontologiju

**Prednosti:**
- ✅ Automatska ekstrakcija
- ✅ Generalizuje na nove termine
- ✅ Bolja pokrivenost

**Mane:**
- ❌ Zahteva model setup
- ❌ Sporije izvršavanje
- ❌ Potreban training data

### Pristup 3: LLM ekstrakcija (SPORO, najbolji kvalitet)
**Vreme:** 1-2 sata implementacija  
**Kvalitet:** Odličan (razume kontekst)

1. Koristiti Ollama/GPT za ekstrakciju slotova
2. Prompt engineering za action/object/actor
3. Strukturisani output (JSON)
4. Fallback na ontologiju

**Prednosti:**
- ✅ Najbolji kvalitet
- ✅ Razume kontekst i nijanse
- ✅ Fleksibilno

**Mane:**
- ❌ Sporo (1-2s po assertion)
- ❌ Zahteva LLM
- ❌ Nedeterministično

## Preporuka: Hibridni pristup

**Faza 1: Brzo rešenje (danas)**
1. Proširiti ontologiju sa osnovnim terminima za radne odnose
2. Re-ekstraktovati assertions
3. Testirati conflict detection
4. **Cilj:** Postići >50% recall na gold cases

**Faza 2: Dugoročno rešenje (sledeća nedelja)**
1. Implementirati NER model za automatsku ekstrakciju
2. Kombinovati sa ontologijom (NER + ontology matching)
3. **Cilj:** Postići >80% recall na gold cases

## Implementacija Faze 1

### Korak 1: Analizirati pilot corpus termine
```python
# Ekstraktovati najčešće reči iz assertions
# Identifikovati actors, actions, objects
```

### Korak 2: Kreirati labor_relations_sr.json
```json
{
  "version": "0.1.0",
  "language": "sr",
  "actors": {
    "employee": {
      "labels": ["zaposleni", "radnik", "radnika", "radniku"]
    },
    "employer": {
      "labels": ["poslodavac", "poslodavca", "poslodavcu"]
    },
    "trade_union": {
      "labels": ["sindikat", "sindikata", "sindikatu"]
    },
    "labor_inspection": {
      "labels": ["inspekcija rada", "inspekcije rada"]
    }
  },
  "actions": {
    "conclude_contract": {
      "labels": ["zaključuje ugovor", "zaključivanje ugovora"]
    },
    "notify": {
      "labels": ["obaveštava", "obavesti", "obaveštavanje"]
    },
    "pay_salary": {
      "labels": ["isplaćuje zaradu", "isplata zarade"]
    },
    "terminate_contract": {
      "labels": ["otkazuje ugovor", "otkaz ugovora"]
    }
  },
  "objects": {
    "employment_contract": {
      "labels": ["ugovor o radu", "ugovora o radu"]
    },
    "salary": {
      "labels": ["zarada", "zarade", "zaradu", "minimalac", "minimalna zarada"]
    },
    "annual_leave": {
      "labels": ["godišnji odmor", "godišnjeg odmora"]
    }
  }
}
```

### Korak 3: Re-ekstraktovati assertions
```bash
# Obrisati stare assertions
# Pokrenuti ekstrakciju ponovo
# Sačuvati u bazu
```

### Korak 4: Testirati
```bash
python scripts/run_evaluation.py
# Očekivano: >50% recall
```

## Procena vremena

| Korak | Vreme | Status |
|-------|-------|--------|
| 1. Analizirati termine | 15 min | ⏭️ |
| 2. Kreirati ontologiju | 30 min | ⏭️ |
| 3. Re-ekstraktovati | 5 min | ⏭️ |
| 4. Testirati | 10 min | ⏭️ |
| **UKUPNO** | **60 min** | |

## Sledeći koraci

1. ✅ Dokumentovati plan (ovaj fajl)
2. ⏭️ Analizirati pilot corpus termine
3. ⏭️ Kreirati labor_relations_sr.json
4. ⏭️ Re-ekstraktovati assertions
5. ⏭️ Testirati conflict detection
6. ⏭️ Dokumentovati rezultate