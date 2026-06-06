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
└──────┬───────┘         │ - name       │         │ - language   │
       │                 │ - language   │         │ - status     │
       │                 │ - created_at │         └──────┬───────┘
       │                 └──────┬───────┘                │
       │ 1                      │                        │ 1
       │                        │ 1                      │
       │ *                      │                        │ *
┌──────┴───────┐                │ *                      │
│ConflictRule  │         ┌──────┴───────┐        ┌──────┴───────┐
│     Set      │         │ OntologyTerm │        │  CorpusRun   │
│              │         │              │        │              │
│ - id         │         │ - id         │        │ - id         │
│ - domain_id  │         │ - set_id     │        │ - corpus_id  │
│ - name       │         │ - name       │        │ - param_set  │
│ - version    │         │ - term       │        │ - ontology   │
│ - desc       │         │ - language   │        │ - conflict   │
└──────┬───────┘         │ - rule       │        │ - status     │
       │                 │ - type       │        │ - started_at │
       │ 1               └──────────────┘        │ - ended_at   │
       │                                         └──────────────┘
       │ *
┌──────┴───────┐
│ConflictRule  │                                  ┌─────────────┐
│              │                                  │  Document   │
│ - id         │                                  │             │
│ - set_id     │                                  │ - id        │
│ - type       │                                  │ - corpus_id │
│ - pattern    │                                  │ - language  │
│ - severity   │                                  │ - filename  │
└──────────────┘                                  │ - title     │
                                                  │ - type      │
       ┌──────────────┐                          │ - is_draft  │
       │   ParamSet   │                          └──────┬──────┘
       │              │                                 │
       │ - id         │                                 │ 1
       │ - name       │                                 │
       │ - llm_model  │                                 │ *
       │ - llm_temp   │                           ┌─────┴────────┐
       │ - ontology   │                           │  LegalUnit   │
       │ - conflict   │                           │              │
       │ - created_at │                           │ - id         │
       └──────────────┘                           │ - doc_id     │
                                                  │ - language   │
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
                                                  │ - language   │
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
                                                  │ - language   │
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

## Osnovni Entiteti

### 0. Domain (Domen)

**Svrha**: Predstavlja pravnu oblast ili domenu (npr. Radno pravo, Šumarstvo, Bezbednost hrane).

**Atributi**:
- `id` (UUID) - Jedinstveni identifikator
- `name` (string) - Naziv domena (npr. "Radno pravo", "Forestry Law", "Lebensmittelsicherheit")
- `description` (text) - Opis domena
- `created_at` (timestamp) - Vreme kreiranja
- `created_by` (string) - Ko je kreirao

**Kompletan Spisak Pravnih Domena (50 kategorija)**:

### I. USTAVNO I UPRAVNO PRAVO
1. Ustavno pravo - Ustav, ustavni zakoni, ljudska prava
2. Upravno pravo - Upravni postupak, upravni akti
3. Lokalna samouprava - Opštine, gradovi, pokrajine

### II. GRAĐANSKO PRAVO
4. Obligaciono pravo - Ugovori, obligacije, odgovornost
5. Stvarno pravo - Svojina, posed, službenosti
6. Porodično pravo - Brak, razvod, starateljstvo
7. Nasledno pravo - Testamenti, zakonsko nasleđivanje

### III. PRIVREDNO PRAVO
8. Privredno pravo - Privredna društva, trgovina
9. Radno pravo - Radni odnosi, zaposleni, poslodavci
10. Intelektualna svojina - Patenti, žigovi, autorska prava
11. Bankovno pravo - Banke, hartije od vrednosti
12. Pravo osiguranja - Životno, imovinsko osiguranje

### IV. KRIVIČNO PRAVO
13. Krivično materijalno pravo - Krivična dela, kazne
14. Krivično procesno pravo - Krivični postupak
15. Izvršenje krivičnih sankcija - Zatvorski sistem

### V. JAVNE FINANSIJE
16. Budžetski sistem - Državni i lokalni budžeti
17. Poreski sistem - Porez na dohodak, PDV, akcize
18. Javne nabavke - Postupci nabavki, ugovori

### VI. SOCIJALNA ZAŠTITA
19. Socijalna zaštita - Socijalna pomoć, dečja zaštita
20. Penzijsko osiguranje - Penzije, invalidnine
21. Zdravstveno osiguranje - Obavezno i dopunsko

### VII. OBRAZOVANJE I KULTURA
22. Obrazovanje - Predškolsko, osnovno, srednje, visoko
23. Nauka i tehnologija - Naučnoistraživački rad
24. Kultura i umetnost - Kulturna dobra, muzeji
25. Sport - Sportske organizacije

### VIII. INFRASTRUKTURA
26. Saobraćaj - Drumski, železnički, vazdušni, rečni
27. Telekomunikacije - Elektronske komunikacije
28. Energetika - Električna energija, gas, obnovljivi izvori
29. Građevinarstvo - Izgradnja, urbanizam, prostorno planiranje

### IX. ŽIVOTNA SREDINA
30. Zaštita životne sredine - Vazduh, voda, zemljište, otpad
31. Šumarstvo - Šume, gazdovanje šumama
32. Vodoprivreda - Vodotokovi, vodne dozvole
33. Poljoprivreda - Poljoprivredno zemljište, subvencije
34. Lovstvo i ribarstvo - Lovišta, ribolovna područja

### X. ZDRAVSTVO I BEZBEDNOST
35. Zdravstvena zaštita - Zdravstvene ustanove, lekovi
36. Bezbednost hrane - Proizvodnja, distribucija hrane
37. Veterinarstvo - Zdravlje životinja
38. Zaštita od požara - Protivpožarna zaštita
39. Zaštita od nepogoda - Poplave, zemljotresi

### XI. BEZBEDNOST I ODBRANA
40. Odbrana - Vojska, vojna obaveza
41. Unutrašnji poslovi - Policija, javni red i mir
42. Bezbednosne službe - BIA, VOA

### XII. SPOLJNI POSLOVI
43. Spoljni poslovi - Diplomatski odnosi
44. Međunarodni ugovori - Ratifikacija ugovora

### XIII. PRAVOSUĐE
45. Sudski sistem - Organizacija sudova, sudije
46. Javno tužilaštvo - Tužioci, krivično gonjenje
47. Advokatska komora - Advokati, pravna pomoć
48. Izvršenje i obezbeđenje - Izvršitelji, prinudno izvršenje

### XIV. MEDIJI I INFORMISANJE
49. Mediji - Štampa, radio, televizija
50. Slobodan pristup informacijama - Javnost rada

**Primer JSON**:
```json
{
  "id": "dom-001",
  "name": "Radno pravo",
  "description": "Propisi koji regulišu odnose između poslodavaca i zaposlenih",
  "created_at": "2026-01-15T10:00:00Z",
  "created_by": "admin"
}
```

**Relacioni Odnosi**:
- `Domain` → `OntologySet` (1:N) - Domen ima više verzija ontologije
- `Domain` → `ConflictRuleSet` (1:N) - Domen ima više verzija pravila
- `Domain` → `Corpus` (1:N) - Domen ima više korpusa

---

## Novi Entiteti u V3

### 1. OntologySet (Verzionisana Ontologija)

**Svrha**: Instanca ontološkog rečnika sa verzionisanjem.

**Atributi**:
- `id` (UUID) - Jedinstveni identifikator
- `domain_id` (UUID) - Domen kome pripada
- `version` (string) - Verzija (npr. "1.0", "2.1")
- `name` (string) - Naziv (npr. "Radno pravo - osnovna verzija")
- `language` (string) - Jezik (npr. "sr", "en", "de")
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
  "language": "sr",
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
- `term` (string) - Termin (npr. "radni odnos")
- `language` (string) - Jezik (npr. "sr", "en", "de")
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
  "language": "sr",
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

---

## Ažurirani Postojeći Entiteti

### Corpus (sa language)

**Novi Atributi**:
- `language` (string) - Jezik korpusa (npr. "sr", "en", "de")

**Primer**:
```json
{
  "id": "corpus-001",
  "name": "Radno pravo - Srbija",
  "domain_id": "dom-001",
  "language": "sr",
  "status": "active"
}
```

---

### Document (sa language, bez corpus_run_id)

**Novi Atributi**:
- `language` (string) - Jezik dokumenta (npr. "sr", "en", "de")

**Napomena**: `corpus_run_id` je uklonjen - Document je povezan samo sa Corpus

**Primer**:
```json
{
  "id": "doc-001",
  "corpus_id": "corpus-001",
  "language": "sr",
  "filename": "zakon_o_radu.txt",
  "title": "Zakon o radu",
  "type": "zakon",
  "is_draft": false
}
```

---

### LegalUnit (sa language, bez corpus_run_id)

**Novi Atributi**:
- `language` (string) - Jezik pravne jedinice (npr. "sr", "en", "de")

**Napomena**: `corpus_run_id` je uklonjen

**Primer**:
```json
{
  "id": "unit-001",
  "document_id": "doc-001",
  "language": "sr",
  "unit_type": "clan",
  "number": "15",
  "title": "Radno vreme",
  "content": "Puno radno vreme iznosi 40 časova nedeljno."
}
```

---

### Assertion (sa language, bez corpus_run_id)

**Novi Atributi**:
- `language` (string) - Jezik asercije (npr. "sr", "en", "de")

**Napomena**: `corpus_run_id` je uklonjen

**Primer**:
```json
{
  "id": "assert-001",
  "legal_unit_id": "unit-001",
  "language": "sr",
  "type": "obligation",
  "content": "Puno radno vreme iznosi 40 časova nedeljno",
  "entities": ["radno_vreme", "40_casova"]
}
```

---

### Embedding (sa language, bez corpus_run_id)

**Novi Atributi**:
- `language` (string) - Jezik embedding-a (npr. "sr", "en", "de")

**Napomena**: `corpus_run_id` je uklonjen

**Primer**:
```json
{
  "id": "emb-001",
  "assertion_id": "assert-001",
  "language": "sr",
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
    language TEXT NOT NULL,
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
    language TEXT NOT NULL,
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
ALTER TABLE corpora ADD COLUMN language TEXT NOT NULL DEFAULT 'sr';
ALTER TABLE documents ADD COLUMN language TEXT NOT NULL DEFAULT 'sr';
ALTER TABLE legal_units ADD COLUMN language TEXT NOT NULL DEFAULT 'sr';
ALTER TABLE assertions ADD COLUMN language TEXT NOT NULL DEFAULT 'sr';
ALTER TABLE embeddings ADD COLUMN language TEXT NOT NULL DEFAULT 'sr';
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

# 3. Pipeline kreira entitete sa language atributom
for document in corpus:
    doc = create_document(corpus_id="corpus-001", language="sr")
    for legal_unit in extract_units(doc):
        unit = create_legal_unit(document_id=doc.id, language="sr")
        for assertion in extract_assertions(unit):
            assert = create_assertion(legal_unit_id=unit.id, language="sr")
            emb = create_embedding(assertion_id=assert.id, language="sr")

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
# Kreira novi CorpusRun i importuje sve entitete
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

### 4. Multi-Language Support

- **language atribut**: Corpus, Document, LegalUnit, Assertion, Embedding, OntologySet, OntologyTerm
- **Fleksibilnost**: Podrška za više jezika (sr, en, de, itd.)
- **Izolacija**: Svaki jezik ima svoje ontologije i termine

### 5. Tracking

- **CorpusRun**: Tracking svih run-ova sa parametrima
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
    name="Default Ontology",
    language="sr"
)

# 2. Migruj postojeće termine
for term in old_ontology_terms:
    create_ontology_term(
        set_id=default_ontology_set.id,
        name=term.name,
        term=term.term,
        language="sr"
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

# 6. Dodaj language atribut svim entitetima
UPDATE corpora SET language = 'sr' WHERE language IS NULL;
UPDATE documents SET language = 'sr' WHERE language IS NULL;
UPDATE legal_units SET language = 'sr' WHERE language IS NULL;
UPDATE assertions SET language = 'sr' WHERE language IS NULL;
UPDATE embeddings SET language = 'sr' WHERE language IS NULL;

# 7. Kreiraj CorpusRun za postojeće korpuse
for corpus in existing_corpora:
    corpus_run = create_corpus_run(
        corpus_id=corpus.id,
        param_set_id=default_param_set.id,
        ontology_set_id=default_ontology_set.id,
        conflict_rule_set_id=default_rule_set.id,
        status="completed"
    )
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
4. **Multi-Language Support**: language atribut u Corpus, Document, LegalUnit, Assertion, Embedding, OntologySet, OntologyTerm
5. **Poređenje**: Poređenje različitih konfiguracija

Ovo omogućava:
- Reprodukciju rezultata
- A/B testiranje
- Laku migraciju između sistema
- Tracking performansi
- Rollback na prethodne verzije
- Podrška za više jezika (sr, en, de, itd.)