# Performance Analiza Draft Review Pipeline-a

## Datum: 2026-06-05

## Timing Rezultati (Test Run)

**Ukupno vreme**: 113.78 sekundi (~1.9 minuta)

### Top 3 Bottleneck-a (97.9% ukupnog vremena):

1. **Hybrid Search: 51.50s (45.3%)**
   - Najsporiji korak u celom pipeline-u
   - Retrieval related corpus units
   - Lokacija: `_retrieve_related_corpus_units` metoda

2. **Load Corpus Documents: 43.67s (38.4%)**
   - Drugi najsporiji korak
   - Učitavanje 235 dokumenata iz korpusa
   - Lokacija: `_load_corpus_documents` metoda

3. **Evaluate Conflicts: 16.16s (14.2%)**
   - Evaluacija konflikata između draft i corpus assertions
   - Lokacija: `get_conflict_registry_service().evaluate_assertion_conflicts()`

### Ostali Koraci (2.1% ukupnog vremena):

- Run checkers: 1.38s (1.2%)
- Save results: 0.61s (0.5%)
- Extract corpus assertions: 0.44s (0.4%) - **CACHE RADI!**
- Svi ostali koraci: < 0.01s

## Analiza

### 1. Hybrid Search (51.50s - 45.3%)

**Problem**: Hybrid search je daleko najsporiji korak.

**Mogući uzroci**:
- Pretraga kroz 235 dokumenata u Qdrant-u
- Kombinacija dense + sparse search
- Reranking rezultata
- Network latency (iako je embedded Qdrant)

**Preporuke za optimizaciju**:
- Smanjiti broj dokumenata za pretragu (filtriranje po relevantnosti)
- Optimizovati Qdrant konfiguraciju (HNSW parametri)
- Razmotriti caching search rezultata za slične query-je
- Paralelizovati multiple search operacije ako ih ima

### 2. Load Corpus Documents (43.67s - 38.4%)

**Problem**: Učitavanje 235 dokumenata traje skoro isto kao hybrid search.

**Mogući uzroci**:
- Čitanje sa diska (SQLite ili fajl sistem)
- Deserijalizacija JSON-a
- Nema cachinga

**Preporuke za optimizaciju**:
- **PRIORITET**: Implementirati in-memory cache za corpus documents
- Lazy loading - učitavati samo potrebne dokumente
- Batch loading sa connection pooling
- Razmotriti Redis cache za corpus documents

### 3. Evaluate Conflicts (16.16s - 14.2%)

**Problem**: Evaluacija konflikata traje relativno dugo.

**Mogući uzroci**:
- LLM inference za svaki conflict candidate
- Kompleksna logika evaluacije
- Veliki broj assertion parova za proveru

**Preporuke za optimizaciju**:
- Paralelizovati LLM pozive
- Implementirati batch inference
- Pre-filtrirati očigledno nekonfliktne parove
- Cache LLM rezultate za slične assertion parove

### 4. Extract Corpus Assertions (0.44s - 0.4%)

**USPEH**: Cache optimizacija radi odlično!
- Prethodno: 60-90 sekundi
- Sada: 0.44 sekundi
- **Poboljšanje: 136-204x brže!**

## Prioriteti za Optimizaciju

### Kratkoročno (Najveći Impact):

1. **Cache Corpus Documents** (očekivano poboljšanje: -40s, 35%)
   - Implementirati sličan cache kao za assertions
   - Potencijalno smanjenje sa 43.67s na ~1s

2. **Optimizovati Hybrid Search** (očekivano poboljšanje: -30s, 26%)
   - Qdrant HNSW tuning
   - Smanjiti broj dokumenata za search
   - Potencijalno smanjenje sa 51.50s na ~20s

3. **Paralelizovati Conflict Evaluation** (očekivano poboljšanje: -10s, 9%)
   - Batch LLM inference
   - Async processing
   - Potencijalno smanjenje sa 16.16s na ~6s

### Dugoročno:

4. Implementirati Redis cache za često korišćene podatke
5. Optimizovati database queries (indexing, connection pooling)
6. Razmotriti distributed processing za velike korpuse
7. Implementirati incremental processing (ne procesirati sve svaki put)

## Očekivani Rezultati Nakon Optimizacije

**Trenutno**: 113.78s

**Nakon optimizacija**:
- Cache corpus documents: -40s
- Optimizovati hybrid search: -30s
- Paralelizovati conflicts: -10s

**Očekivano**: ~34s (70% brže!)

## Zaključak

Identifikovana su tri glavna bottleneck-a koja čine 97.9% ukupnog vremena:

1. **Hybrid Search** (45.3%) - Najsporiji, potrebna Qdrant optimizacija
2. **Load Corpus Documents** (38.4%) - Potreban cache (kao za assertions)
3. **Evaluate Conflicts** (14.2%) - Potrebna paralelizacija LLM poziva

Cache optimizacija za corpus assertions je bila **izuzetno uspešna** (136-204x brže), što pokazuje da će slične optimizacije za corpus documents i search rezultate doneti značajna poboljšanja.

**Sledeći korak**: Implementirati cache za corpus documents kao prioritet #1.