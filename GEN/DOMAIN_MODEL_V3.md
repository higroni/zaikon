# ZAIKON - Domain Model V3 (Production-Ready)

**Version**: 3.0  
**Last Updated**: 2026-06-06  
**Status**: Production-Ready with Versioning & Parameterization

---

## Pregled

Ovaj dokument definiše production-ready domain model sa:
- **Verzionisanjem**: OntologySet, ConflictRuleSet, CorpusRun
- **Parametrizacijom**: ParamSet za tracking parametara
- **Export/Import**: Mogućnost izvoza i uvoza "knowledge sets"

---

## Entity Relationship Diagram (V3)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ZAIKON DOMAIN MODEL V3 (PRODUCTION)                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Domain     │ 1     * │ OntologySet  │         │   Corpus     │
│              ├─────────┤              │         │              │
│ - id         │  has    │ - id         │         │ - id         │
│ - name       │         │ - domain_id  │         │ - name       │
│ - desc       │         │ - version    │         │ - domain_id  │
└──────┬───────┘         │ - name       │         │ - status     │
       │                 │ - created_at │         └──────┬───────┘
       │                 └──────┬───────┘                │
       │ 1                      │                        │
       │                        │ 1                      │ 1
       │ *                      │                        │
┌──────┴───────┐                │ *                      │ *
│ConflictRule  │         ┌──────┴───────┐        ┌──────┴───────┐
│     Set      │         │ OntologyTerm │        │  CorpusRun   │
│              │         │              │        │              │
│ - id         │         │ - id         │        │ - id         │
│ - domain_id  │         │ - set_id     │        │ - corpus_id  │
│ - name       │         │ - name       │        │ - param_set  │
│ - version    │         │ - term       │        │ - ontology   │
│ - desc       │         │ - rule       │        │ - conflict   │
└──────┬───────┘         │ - type       │        │ - status     │
       │                 └──────────────┘        │ - started_at │
       │ 1                                       │ - ended_at   │
       │                                         └──────┬───────┘
       │ *                                              │
┌──────┴───────┐                                        │ 1
│ConflictRule  │                                        │
│              │                                        │ *
│ - id         │                                  ┌─────┴────────┐
│ - set_id     │                                  │  Document    │
│ - type       │                                  │              │
│ - pattern    │                                  │ - id         │
│ - severity   │                                  │ - corpus_id  │
└──────────────┘                                  │ - run_id     │
                                                  │ - filename   │
       ┌──────────────┐                          │ - title      │
       │   ParamSet   │                          │ - type       │
       │              │                          │ - is_draft   │
       │ - id         │                          └──────┬───────┘
       │ - name       │                                 │
       │ - llm_model  │                                 │ 1
       │ - llm_temp   │                                 │
       │ - ontology   │                                 │ *
       │ - conflict   │                           ┌─────┴────────┐
       │ - created_at │                           │  LegalUnit   │
       └──────────────┘                           │              │
                                                  │ - id         │
                                                  │ - doc_id     │
                                                  │ - run_id     │
                                                  │ - unit_type  │
                                                  │ - number     │
                                                  │ - title      │
                                                  │ - content    │
                                                  └──────┬───────┘
                                                         │
                                                         │ 1
                                                         │
                                                         │ *
                                                  ┌──────┴───────┐
                                                  │  Assertion   │
                                                  │              │
                                                  │ - id         │
                                                  │ - unit_id    │
                                                  │ - run_id     │
                                                  │ - type       │
                                                  │ - content    │
                                                  │ - entities   │
                                                  └──────┬───────┘
                                                         │
                                                         │ 1
                                                         │
                                                         │ 1
                                                  ┌──────┴───────┐
                                                  │  Embedding   │
                                                  │              │
                                                  │ - id         │
                                                  │ - assert_id  │
                                                  │ - run_id     │
                                                  │ - vector     │
                                                  │ - model      │
                                                  └──────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│ DraftReview  │ 1     * │   Finding    │ *     1 │  Resolution  │
│              ├─────────┤              ├─────────┤              │
│ - id         │  has    │ - id         │  has    │ - id         │
│ - draft_id   │         │ - review_id  │         │ - finding_id │
│ - corpus_id  │         │ - assert1_id │         │ - status     │
│ - param_set  │         │ - assert2_id │         │ - decision   │
│ - status     │         │ - rule_id    │         │ - comment    │
│ - started_at │         │ - severity   │         │ - user       │
└──────────────┘         │ - message    │         │ - timestamp  │
                         └──────────────┘         └──────────────┘
```

---

## Novi Entiteti u V3

### 1. OntologySet (Verzionisana Ontologija)

**Svrha**: Instanca ontološkog rečnika sa verzionisanjem.

**Atributi**:
- `id` (UUID) - Jedinstveni identifikator
- `domain_id` (UUID) - Domen kome pripada
- `version` (string) - Verzija (npr. "1.0", "2.1")
- `name` (string) - Naziv (npr. "Radno pravo - osnovna verzija")
- `description` (text) - Opis izmena u ovoj verziji
- `created_at` (timestamp) - Vreme kreiranja
- `created_by` (string) - Ko je kreirao

**Primer**:
```json
{
  "id": "ont-set-001",
  "domain_id": "dom-001",
  "version": "1.0",
  "name": "Radno pravo - osnovna verzija",
  "description": "Početna verzija sa osnovnim terminima",
  "created_at": "2026-01-15T10:00:00Z",
  "created_by": "admin"
}
```

**Relacioni Odnosi**:
- `Domain` → `OntologySet` (1:N) - Domen ima više verzija ontologije
- `OntologySet` → `OntologyTerm` (1:N) - Set sadrži termine
- `CorpusRun` → `OntologySet` (N:1) - Run koristi određenu verziju

---

### 2. OntologyTerm (Ontološki Termin)

**Svrha**: Pojedinačni ontološki objekat (termin ili pravilo).

**Atributi**:
- `id` (UUID) - Jedinstveni identifikator
- `set_id` (UUID) - OntologySet kome pripada
- `name` (string) - Naziv termina (npr. "radni_odnos")
- `term` (string) - Termin na srpskom (npr. "radni odnos")
- `rule` (text) - Pravilo ili definicija (opciono)
- `type` (enum) - Tip: "entity", "relation", "rule"
- `metadata` (JSON) - Dodatni podaci

**Primer**:
```json
{
  "id": "term-001",
  "set_id": "ont-set-001",
  "name": "radni_odnos",
  "term": "radni odnos",
  "rule": "Odnos između poslodavca i zaposlenog",
  "type": "entity",
  "metadata": {
    "synonyms": ["zaposlenje", "radni angažman"],
    "category": "osnovno"
  }
}
```

**Relacioni Odnosi**:
- `OntologySet` → `OntologyTerm` (1:N) - Set sadrži termine

---

### 3. ConflictRuleSet (Verzionisan Skup Pravila)

**Svrha**: Verzionisan skup pravila za detekciju konflikata (preimenovano iz ConflictSet).

**Atributi**:
- `id` (UUID) - Jedinstveni identifikator
- `domain_id` (UUID) - Domen kome pripada
- `version` (string) - Verzija (npr. "1.0", "2.1")
- `name` (string) - Naziv
- `description` (text) - Opis
- `created_at` (timestamp) - Vreme kreiranja
- `created_by` (string) - Ko je kreirao

**Primer**:
```json
{
  "id": "rule-set-001",
  "domain_id": "dom-001",
  "version": "1.0",
  "name": "Radno pravo - osnovna pravila",
  "description": "Početna verzija sa 127 pravila",
  "created_at": "2026-01-15T10:00:00Z",
  "created_by": "admin"
}
```

**Relacioni Odnosi**:
- `Domain` → `ConflictRuleSet` (1:N) - Domen ima više verzija pravila
- `ConflictRuleSet` → `ConflictRule` (1:N) - Set sadrži pravila
- `CorpusRun` → `ConflictRuleSet` (N:1) - Run koristi određenu verziju

---

### 4. ParamSet (Set Parametara)

**Svrha**: Pamti parametre sa kojima je pokrenut određeni job.

**Atributi**:
- `id` (UUID) - Jedinstveni identifikator
- `name` (string) - Naziv (npr. "Production Config v1")
- `llm_model` (string) - LLM model (npr. "gpt-4")
- `llm_temperature` (float) - Temperatura (npr. 0.7)
- `llm_max_tokens` (int) - Max tokeni
- `ontology_set_id` (UUID) - Verzija ontologije
- `conflict_rule_set_id` (UUID) - Verzija pravila
- `embedding_model` (string) - Model za embeddings
- `chunk_size` (int) - Veličina chunk-a
- `chunk_overlap` (int) - Overlap između chunk-ova
- `vector_weight` (float) - Težina vektorske pretrage (0.45)
- `keyword_weight` (float) - Težina keyword pretrage (0.35)
- `graph_weight` (float) - Težina graph pretrage (0.20)
- `reranker_model` (string) - Reranker model
- `top_k` (int) - Broj rezultata
- `metadata` (JSON) - Dodatni parametri
- `created_at` (timestamp) - Vreme kreiranja
- `created_by` (string) - Ko je kreirao

**Primer**:
```json
{
  "id": "param-001",
  "name": "Production Config v1",
  "llm_model": "gpt-4",
  "llm_temperature": 0.7,
  "llm_max_tokens": 2000,
  "ontology_set_id": "ont-set-001",
  "conflict_rule_set_id": "rule-set-001",
  "embedding_model": "text-embedding-3-large",
  "chunk_size": 512,
  "chunk_overlap": 50,
  "vector_weight": 0.45,
  "keyword_weight": 0.35,
  "graph_weight": 0.20,
  "reranker_model": "cross-encoder/ms-marco-MiniLM-L-12-v2",
  "top_k": 10,
  "metadata": {},
  "created_at": "2026-01-15T10:00:00Z",
  "created_by": "admin"
}
```

**Relacioni Odnosi**:
- `ParamSet` → `OntologySet` (N:1) - Parametri koriste verziju ontologije
- `ParamSet` → `ConflictRuleSet` (N:1) - Parametri koriste verziju pravila
- `CorpusRun` → `ParamSet` (N:1) - Run koristi set parametara
- `DraftReview` → `ParamSet` (N:1) - Review koristi set parametara

---

### 5. CorpusRun (Run Obrade Korpusa)

**Svrha**: Pamti run obrade korpusa sa određenim parametrima. Omogućava export/import "knowledge sets".

**Atributi**:
- `id` (UUID) - Jedinstveni identifikator
- `corpus_id` (UUID) - Korpus koji se obrađuje
- `param_set_id` (UUID) - Set parametara
- `ontology_set_id` (UUID) - Verzija ontologije
- `conflict_rule_set_id` (UUID) - Verzija pravila
- `status` (enum) - Status: "running", "completed", "failed"
- `started_at` (timestamp) - Vreme početka
- `ended_at` (timestamp) - Vreme završetka
- `documents_processed` (int) - Broj obrađenih dokumenata
- `legal_units_extracted` (int) - Broj ekstraktovanih jedinica
- `assertions_extracted` (int) - Broj ekstraktovanih asercija
- `embeddings_created` (int) - Broj kreiranih embeddings
- `error_message` (text) - Poruka o grešci (ako failed)
- `metadata` (JSON) - Dodatni podaci

**Primer**:
```json
{
  "id": "run-001",
  "corpus_id": "corpus-001",
  "param_set_id": "param-001",
  "ontology_set_id": "ont-set-001",
  "conflict_rule_set_id": "rule-set-001",
  "status": "completed",
  "started_at": "2026-01-15T10:00:00Z",
  "ended_at": "2026-01-15T10:15:00Z",
  "documents_processed": 50,
  "legal_units_extracted": 1250,
  "assertions_extracted": 3500,
  "embeddings_created": 3500,
  "error_message": null,
  "metadata": {
    "pipeline_version": "1.0",
    "worker_count": 4
  }
}
```

**Relacioni Odnosi**:
- `Corpus` → `CorpusRun` (1:N) - Korpus ima više run-ova
- `CorpusRun` → `ParamSet` (N:1) - Run koristi set parametara
- `CorpusRun` → `OntologySet` (N:1) - Run koristi verziju ontologije
- `CorpusRun` → `ConflictRuleSet` (N:1) - Run koristi verziju pravila
- `CorpusRun` → `Document` (1:N) - Run kreira dokumente
- `CorpusRun` → `LegalUnit` (1:N) - Run kreira pravne jedinice
- `CorpusRun` → `Assertion` (1:N) - Run kreira asercije
- `CorpusRun` → `Embedding` (1:N) - Run kreira embeddings

---

## Ažurirani Postojeći Entiteti

### Document (sa corpus_run_id)

**Novi Atributi**:
- `corpus_run_id` (UUID) - Run koji je kreirao dokument

**Primer**:
```json
{
  "id": "doc-001",
  "corpus_id": "corpus-001",
  "corpus_run_id": "run-001",
  "filename": "zakon_o_radu.txt",
  "title": "Zakon o radu",
  "type": "zakon",
  "is_draft": false
}
```

---

### LegalUnit (sa corpus_run_id)

**Novi Atributi**:
- `corpus_run_id` (UUID) - Run koji je kreirao pravnu jedinicu

**Primer**:
```json
{
  "id": "unit-001",
  "document_id": "doc-001",
  "corpus_run_id": "run-001",
  "unit_type": "clan",
  "number": "15",
  "title": "Radno vreme",
  "content": "Puno radno vreme iznosi 40 časova nedeljno."
}
```

---

### Assertion (sa corpus_run_id)

**Novi Atributi**:
- `corpus_run_id` (UUID) - Run koji je kreirao aserciju

**Primer**:
```json
{
  "id": "assert-001",
  "legal_unit_id": "unit-001",
  "corpus_run_id": "run-001",
  "type": "obligation",
  "content": "Puno radno vreme iznosi 40 časova nedeljno",
  "entities": ["radno_vreme", "40_casova"]
}
```

---

### Embedding (sa corpus_run_id)

**Novi Atributi**:
- `corpus_run_id` (UUID) - Run koji je kreirao embedding

**Primer**:
```json
{
  "id": "emb-001",
  "assertion_id": "assert-001",
  "corpus_run_id": "run-001",
  "vector": [0.123, -0.456, ...],
  "model": "text-embedding-3-large"
}
```

---

### DraftReview (sa param_set_id)

**Novi Atributi**:
- `param_set_id` (UUID) - Set parametara korišćen za review

**Primer**:
```json
{
  "id": "review-001",
  "draft_document_id": "doc-draft-001",
  "corpus_id": "corpus-001",
  "param_set_id": "param-001",
  "status": "completed",
  "started_at": "2026-01-15T11:00:00Z",
  "ended_at": "2026-01-15T11:05:00Z"
}
```

---

## Export/Import "Knowledge Sets"

### Export CorpusRun

**Endpoint**: `GET /api/v1/corpus-runs/{run_id}/export`

**Response**:
```json
{
  "corpus_run": {
    "id": "run-001",
    "corpus_id": "corpus-001",
    "param_set_id": "param-001",
    "status": "completed",
    "started_at": "2026-01-15T10:00:00Z",
    "ended_at": "2026-01-15T10:15:00Z"
  },
  "param_set": {
    "id": "param-001",
    "name": "Production Config v1",
    "llm_model": "gpt-4",
    "llm_temperature": 0.7,
    ...
  },
  "ontology_set": {
    "id": "ont-set-001",
    "version": "1.0",
    "terms": [...]
  },
  "conflict_rule_set": {
    "id": "rule-set-001",
    "version": "1.0",
    "rules": [...]
  },
  "documents": [...],
  "legal_units": [...],
  "assertions": [...],
  "embeddings": [...]
}
```

### Import CorpusRun

**Endpoint**: `POST /api/v1/corpus-runs/import`

**Request**:
```json
{
  "corpus_run": {...},
  "param_set": {...},
  "ontology_set": {...},
  "conflict_rule_set": {...},
  "documents": [...],
  "legal_units": [...],
  "assertions": [...],
  "embeddings": [...]
}
```

**Proces**:
1. Kreira novi `CorpusRun` sa istim parametrima
2. Importuje sve povezane entitete
3. Ažurira `corpus_run_id` u svim entitetima
4. Vraća novi `corpus_run_id`

---

## Poređenje Parametara

### Endpoint: `GET /api/v1/param-sets/compare`

**Query Params**:
- `param_set_1` (UUID)
- `param_set_2` (UUID)

**Response**:
```json
{
  "param_set_1": {
    "id": "param-001",
    "name": "Production Config v1",
    "llm_temperature": 0.7,
    "vector_weight": 0.45
  },
  "param_set_2": {
    "id": "param-002",
    "name": "Experimental Config",
    "llm_temperature": 0.9,
    "vector_weight": 0.50
  },
  "differences": [
    {
      "field": "llm_temperature",
      "value_1": 0.7,
      "value_2": 0.9
    },
    {
      "field": "vector_weight",
      "value_1": 0.45,
      "value_2": 0.50
    }
  ],
  "performance_comparison": {
    "param_set_1": {
      "avg_processing_time": "15m",
      "avg_conflicts_found": 127,
      "success_rate": 0.98
    },
    "param_set_2": {
      "avg_processing_time": "18m",
      "avg_conflicts_found": 145,
      "success_rate": 0.95
    }
  }
}
```

---

## Storage Mapping (V3)

### SQLite Tables

```sql
-- Novi entiteti
CREATE TABLE ontology_sets (
    id TEXT PRIMARY KEY,
    domain_id TEXT NOT NULL,
    version TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL,
    created_by TEXT NOT NULL,
    FOREIGN KEY (domain_id) REFERENCES domains(id)
);

CREATE TABLE ontology_terms (
    id TEXT PRIMARY KEY,
    set_id TEXT NOT NULL,
    name TEXT NOT NULL,
    term TEXT NOT NULL,
    rule TEXT,
    type TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (set_id) REFERENCES ontology_sets(id)
);

CREATE TABLE conflict_rule_sets (
    id TEXT PRIMARY KEY,
    domain_id TEXT NOT NULL,
    version TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL,
    created_by TEXT NOT NULL,
    FOREIGN KEY (domain_id) REFERENCES domains(id)
);

CREATE TABLE conflict_rules (
    id TEXT PRIMARY KEY,
    set_id TEXT NOT NULL,
    type TEXT NOT NULL,
    pattern TEXT NOT NULL,
    severity TEXT NOT NULL,
    FOREIGN KEY (set_id) REFERENCES conflict_rule_sets(id)
);

CREATE TABLE param_sets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    llm_model TEXT NOT NULL,
    llm_temperature REAL NOT NULL,
    llm_max_tokens INTEGER NOT NULL,
    ontology_set_id TEXT NOT NULL,
    conflict_rule_set_id TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    chunk_size INTEGER NOT NULL,
    chunk_overlap INTEGER NOT NULL,
    vector_weight REAL NOT NULL,
    keyword_weight REAL NOT NULL,
    graph_weight REAL NOT NULL,
    reranker_model TEXT NOT NULL,
    top_k INTEGER NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP NOT NULL,
    created_by TEXT NOT NULL,
    FOREIGN KEY (ontology_set_id) REFERENCES ontology_sets(id),
    FOREIGN KEY (conflict_rule_set_id) REFERENCES conflict_rule_sets(id)
);

CREATE TABLE corpus_runs (
    id TEXT PRIMARY KEY,
    corpus_id TEXT NOT NULL,
    param_set_id TEXT NOT NULL,
    ontology_set_id TEXT NOT NULL,
    conflict_rule_set_id TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    documents_processed INTEGER,
    legal_units_extracted INTEGER,
    assertions_extracted INTEGER,
    embeddings_created INTEGER,
    error_message TEXT,
    metadata TEXT,
    FOREIGN KEY (corpus_id) REFERENCES corpora(id),
    FOREIGN KEY (param_set_id) REFERENCES param_sets(id),
    FOREIGN KEY (ontology_set_id) REFERENCES ontology_sets(id),
    FOREIGN KEY (conflict_rule_set_id) REFERENCES conflict_rule_sets(id)
);

-- Ažurirane tabele
ALTER TABLE documents ADD COLUMN corpus_run_id TEXT;
ALTER TABLE legal_units ADD COLUMN corpus_run_id TEXT;
ALTER TABLE assertions ADD COLUMN corpus_run_id TEXT;
ALTER TABLE embeddings ADD COLUMN corpus_run_id TEXT;
ALTER TABLE draft_reviews ADD COLUMN param_set_id TEXT;
```

---

## API Endpoints (V3)

### OntologySet Management

```
GET    /api/v1/ontology-sets                    # List all sets
GET    /api/v1/ontology-sets/{id}               # Get specific set
POST   /api/v1/ontology-sets                    # Create new set
PUT    /api/v1/ontology-sets/{id}               # Update set
DELETE /api/v1/ontology-sets/{id}               # Delete set
GET    /api/v1/ontology-sets/{id}/terms         # Get terms in set
POST   /api/v1/ontology-sets/{id}/terms         # Add term to set
```

### ConflictRuleSet Management

```
GET    /api/v1/conflict-rule-sets               # List all sets
GET    /api/v1/conflict-rule-sets/{id}          # Get specific set
POST   /api/v1/conflict-rule-sets               # Create new set
PUT    /api/v1/conflict-rule-sets/{id}          # Update set
DELETE /api/v1/conflict-rule-sets/{id}          # Delete set
GET    /api/v1/conflict-rule-sets/{id}/rules    # Get rules in set
POST   /api/v1/conflict-rule-sets/{id}/rules    # Add rule to set
```

### ParamSet Management

```
GET    /api/v1/param-sets                       # List all sets
GET    /api/v1/param-sets/{id}                  # Get specific set
POST   /api/v1/param-sets                       # Create new set
PUT    /api/v1/param-sets/{id}                  # Update set
DELETE /api/v1/param-sets/{id}                  # Delete set
GET    /api/v1/param-sets/compare               # Compare two sets
```

### CorpusRun Management

```
GET    /api/v1/corpus-runs                      # List all runs
GET    /api/v1/corpus-runs/{id}                 # Get specific run
POST   /api/v1/corpus-runs                      # Start new run
GET    /api/v1/corpus-runs/{id}/status          # Get run status
GET    /api/v1/corpus-runs/{id}/export          # Export knowledge set
POST   /api/v1/corpus-runs/import               # Import knowledge set
DELETE /api/v1/corpus-runs/{id}                 # Delete run
```

---

## Data Flow Examples (V3)

### 1. Import Korpusa sa Verzionisanjem

```python
# 1. Kreiraj ParamSet
param_set = {
    "name": "Production Config v1",
    "llm_model": "gpt-4",
    "llm_temperature": 0.7,
    "ontology_set_id": "ont-set-001",
    "conflict_rule_set_id": "rule-set-001",
    ...
}
POST /api/v1/param-sets

# 2. Pokreni CorpusRun
corpus_run = {
    "corpus_id": "corpus-001",
    "param_set_id": "param-001"
}
POST /api/v1/corpus-runs

# 3. Pipeline kreira entitete sa corpus_run_id
for document in corpus:
    doc = create_document(corpus_run_id="run-001")
    for legal_unit in extract_units(doc):
        unit = create_legal_unit(corpus_run_id="run-001")
        for assertion in extract_assertions(unit):
            assert = create_assertion(corpus_run_id="run-001")
            emb = create_embedding(assert, corpus_run_id="run-001")

# 4. Završi CorpusRun
PATCH /api/v1/corpus-runs/run-001
{
    "status": "completed",
    "ended_at": "2026-01-15T10:15:00Z",
    "documents_processed": 50,
    "legal_units_extracted": 1250,
    "assertions_extracted": 3500,
    "embeddings_created": 3500
}
```

### 2. Export/Import Knowledge Set

```python
# Export
GET /api/v1/corpus-runs/run-001/export
# Vraća JSON sa svim entitetima

# Import u novi sistem
POST /api/v1/corpus-runs/import
{
    "corpus_run": {...},
    "param_set": {...},
    "ontology_set": {...},
    "conflict_rule_set": {...},
    "documents": [...],
    "legal_units": [...],
    "assertions": [...],
    "embeddings": [...]
}
# Kreira novi corpus_run_id i importuje sve
```

### 3. Poređenje Parametara

```python
# Uporedi dva seta parametara
GET /api/v1/param-sets/compare?param_set_1=param-001&param_set_2=param-002

# Vraća razlike i performance metrics
{
    "differences": [...],
    "performance_comparison": {
        "param_set_1": {
            "avg_processing_time": "15m",
            "avg_conflicts_found": 127
        },
        "param_set_2": {
            "avg_processing_time": "18m",
            "avg_conflicts_found": 145
        }
    }
}
```

---

## Prednosti V3 Modela

### 1. Verzionisanje

- **OntologySet**: Različite verzije ontologije za različite potrebe
- **ConflictRuleSet**: Različite verzije pravila za testiranje
- **CorpusRun**: Tracking svih run-ova sa parametrima

### 2. Parametrizacija

- **ParamSet**: Centralno mesto za sve parametre
- **Poređenje**: Lako poređenje različitih konfiguracija
- **Reprodukcija**: Mogućnost reprodukcije rezultata

### 3. Export/Import

- **Knowledge Sets**: Export kompletnog seta znanja
- **Migracija**: Lak prenos između sistema
- **Backup**: Jednostavan backup i restore

### 4. Tracking

- **corpus_run_id**: Svaki entitet zna iz kog run-a potiče
- **Performance**: Tracking performansi različitih konfiguracija
- **Debugging**: Lakše debugovanje problema

### 5. Fleksibilnost

- **A/B Testing**: Testiranje različitih konfiguracija
- **Rollback**: Vraćanje na prethodne verzije
- **Eksperimenti**: Lako eksperimentisanje sa parametrima

---

## Migration Strategy (V2 → V3)

### Faza 1: Dodaj Nove Tabele

```sql
-- Kreiraj nove tabele
CREATE TABLE ontology_sets (...);
CREATE TABLE ontology_terms (...);
CREATE TABLE conflict_rule_sets (...);
CREATE TABLE param_sets (...);
CREATE TABLE corpus_runs (...);
```

### Faza 2: Migracija Postojećih Podataka

```python
# 1. Kreiraj default OntologySet
default_ontology_set = create_ontology_set(
    domain_id="dom-001",
    version="1.0",
    name="Default Ontology"
)

# 2. Migruj postojeće termine
for term in old_ontology_terms:
    create_ontology_term(
        set_id=default_ontology_set.id,
        name=term.name,
        term=term.term
    )

# 3. Kreiraj default ConflictRuleSet
default_rule_set = create_conflict_rule_set(
    domain_id="dom-001",
    version="1.0",
    name="Default Rules"
)

# 4. Migruj postojeća pravila
for rule in old_conflict_rules:
    create_conflict_rule(
        set_id=default_rule_set.id,
        type=rule.type,
        pattern=rule.pattern
    )

# 5. Kreiraj default ParamSet
default_param_set = create_param_set(
    name="Default Config",
    ontology_set_id=default_ontology_set.id,
    conflict_rule_set_id=default_rule_set.id,
    ...
)

# 6. Kreiraj CorpusRun za postojeće korpuse
for corpus in existing_corpora:
    corpus_run = create_corpus_run(
        corpus_id=corpus.id,
        param_set_id=default_param_set.id,
        status="completed"
    )
    
    # Ažuriraj corpus_run_id u svim entitetima
    UPDATE documents SET corpus_run_id = corpus_run.id WHERE corpus_id = corpus.id
    UPDATE legal_units SET corpus_run_id = corpus_run.id WHERE document_id IN (...)
    UPDATE assertions SET corpus_run_id = corpus_run.id WHERE legal_unit_id IN (...)
    UPDATE embeddings SET corpus_run_id = corpus_run.id WHERE assertion_id IN (...)
```

### Faza 3: Ažuriraj API

```python
# Ažuriraj sve API endpoint-e da koriste nove entitete
# Dodaj nove endpoint-e za verzionisanje i parametrizaciju
```

---

## Zaključak

Domain Model V3 dodaje:

1. **Verzionisanje**: OntologySet, ConflictRuleSet, CorpusRun
2. **Parametrizaciju**: ParamSet za tracking parametara
3. **Export/Import**: Mogućnost izvoza i uvoza "knowledge sets"
4. **Tracking**: corpus_run_id u svim entitetima
5. **Poređenje**: Poređenje različitih konfiguracija

Ovo omogućava:
- Reprodukciju rezultata
- A/B testiranje
- Laku migraciju između sistema
- Tracking performansi
- Rollback na prethodne verzije