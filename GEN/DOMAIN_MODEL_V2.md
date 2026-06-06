# ZAIKON - Domain Model V2 (Refined)

## Pregled

Ovaj dokument definiše refaktorisani domain model sa logičnijim odnosima između entiteta.

---

## Entity Relationship Diagram (Refined)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ZAIKON DOMAIN MODEL V2 (REFINED)                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Domain     │ *     * │  Ontology    │ *     * │   Corpus     │
│              ├─────────┤              ├─────────┤              │
│ - id         │  uses   │ - id         │  used_by│ - id         │
│ - name       │         │ - name       │         │ - name       │
│ - desc       │         │ - terms      │         │ - domain_id  │
└──────┬───────┘         │ - rules      │         │ - status     │
       │                 └──────────────┘         └──────┬───────┘
       │ 1                                               │
       │                                                 │ 1
       │ *                                               │
┌──────┴───────┐                                         │ *
│ ConflictSet  │                                  ┌──────┴───────┐
│              │                                  │  Document    │
│ - id         │                                  │              │
│ - domain_id  │                                  │ - id         │
│ - name       │                                  │ - corpus_id  │
│ - desc       │                                  │ - filename   │
└──────┬───────┘                                  │ - title      │
       │                                          │ - type       │
       │ 1                                        │ - is_draft   │
       │                                          └──────┬───────┘
       │ *                                              │
┌──────┴───────┐                                        │ 1
│ConflictRule  │                                        │
│              │                                        │ *
│ - id         │                                  ┌─────┴────────┐
│ - set_id     │                                  │  LegalUnit   │
│ - type       │                                  │              │
│ - category   │                                  │ - id         │
│ - logic      │                                  │ - document_id│
│ - severity   │                                  │ - type       │
└──────────────┘                                  │ - number     │
                                                  │ - text       │
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
                                                  │ - doc_id     │
                                                  │ - type       │
                                                  │ - subject    │
                                                  │ - action     │
                                                  │ - object     │
                                                  │ - deadline   │
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
                                                  │ - vector     │
                                                  │ - model      │
                                                  └──────────────┘


┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│ DraftReview  │ 1     * │   Finding    │ *     2 │  Assertion   │
│              ├─────────┤              ├─────────┤              │
│ - id         │ produces│ - id         │ compares│ - id         │
│ - name       │         │ - review_id  │         │ - type       │
│ - draft_id   │         │ - assert1_id │         │ - subject    │
│ - corpus_id  │         │ - assert2_id │         │ - action     │
│ - rule_set_id│         │ - conflict   │         └──────────────┘
│ - status     │         │ - severity   │
│ - created_at │         │ - message    │
└──────┬───────┘         └──────┬───────┘
       │                        │
       │ 1                      │ 1
       │                        │
       │ *                      │ *
┌──────┴───────┐         ┌──────┴───────┐
│  Resolution  │         │              │
│              │         │  (Combined)  │
│ - id         │         │              │
│ - review_id  │         │              │
│ - finding_id │         │              │
│ - status     │         │              │
│ - action     │         │              │
│ - reason     │         │              │
│ - notes      │         │              │
│ - user_id    │         │              │
│ - timestamp  │         │              │
└──────────────┘         └──────────────┘


LEGEND:
─────  1:1 relationship
═════  1:N relationship
┈┈┈┈┈  N:M relationship
```

---

## Ključne Izmene u V2

### 1. Document je Univerzalan Entitet

**Stari pristup:**
- Odvojeni entiteti: Document, DraftDocument, DraftUnit, DraftAssertion

**Novi pristup:**
- **Jedan Document entitet** sa `is_draft` flag-om
- **Jedan LegalUnit entitet** za sve dokumente
- **Jedan Assertion entitet** za sve asercije

**Prednosti:**
- Manje duplikacije koda
- Lakše poređenje (isti tip entiteta)
- Jednostavniji upiti
- Draft može postati corpus document (promeni flag)

---

### 2. Ontology je Vezana za Domain (N:M)

**Stari pristup:**
- Ontology 1:1 sa Corpus

**Novi pristup:**
- **Ontology N:M sa Domain**
- **Ontology N:M sa Corpus**

**Razlog:**
- Ontologija je domen-specifična (npr. "Radno pravo")
- Više korpusa može koristiti istu ontologiju
- Ontologija se može reuse-ovati

**Primer:**
```
Ontology: "Radno pravo - Osnovna"
  ├─ Used by Domain: "Radno pravo"
  ├─ Used by Corpus: "Pilot Radni Odnosi"
  ├─ Used by Corpus: "Zakon o radu 2024"
  └─ Used by Corpus: "Pravilnici o radu"
```

---

### 3. ConflictSet i ConflictRule (Nezavisni Entiteti)

**Novi entiteti:**
- **ConflictSet** - Nezavisan skup pravila koji se može koristiti u više domena
- **ConflictRule** - Pojedinačno pravilo unutar seta

**Razlog:**
- ConflictSet je **nezavisan** od domena
- Isti set pravila može se koristiti u više domena
- Omogućava reusability i konzistentnost
- Lakše održavanje (jedan set, više domena)

**Primer:**
```
ConflictSet: "Standard - Sva pravila"
  ├─ Used by Domain: "Radno pravo"
  ├─ Used by Domain: "Šumarstvo"
  ├─ Used by Domain: "Zdravstvo"
  └─ Contains:
      ├─ ConflictRule: "contradictory_obligation"
      ├─ ConflictRule: "contradictory_deadline"
      ├─ ConflictRule: "hierarchical_violation"
      └─ ... (127 pravila)

ConflictSet: "Strict - Strožija pravila"
  ├─ Used by Domain: "Radno pravo"
  └─ Contains:
      ├─ ConflictRule: "contradictory_obligation" (stricter)
      ├─ ConflictRule: "contradictory_deadline" (stricter)
      └─ ...

ConflictSet: "Radno pravo - Specijalizovana"
  ├─ Used by Domain: "Radno pravo"
  └─ Contains:
      ├─ ConflictRule: "labor_specific_rule_1"
      ├─ ConflictRule: "labor_specific_rule_2"
      └─ ...
```

**Odnosi:**
- **ConflictSet N:M sa Domain** - Jedan set može se koristiti u više domena
- **Domain ima default_conflict_set_id** - Svaki domen ima default set
- **DraftReview bira ConflictSet** - Review može izabrati specifičan set

**Prednosti:**
- ✅ Reusability - Isti set za više domena
- ✅ Konzistentnost - Ista pravila svuda
- ✅ Lakše održavanje - Izmena na jednom mestu
- ✅ Fleksibilnost - Domain-specific setovi kada treba

---

### 4. DraftReview kao Run Sesija

**Novi pristup:**
- **DraftReview** = Jedna sesija analize
- Vezana za: Draft Document, Corpus, ConflictSet
- Proizvodi: Findings

**Atributi:**
```json
{
  "id": "review123",
  "name": "Pravilnik o radu - Analiza 2024-01-20",
  "draft_document_id": "doc456",  // Document sa is_draft=true
  "corpus_id": "corpus789",
  "conflict_set_id": "set111",
  "status": "completed",
  "findings_count": 8,
  "created_at": "2024-01-20T09:00:00Z",
  "completed_at": "2024-01-20T09:05:23Z"
}
```

---

### 5. Finding Povezuje 2 Asercije

**Stari pristup:**
- Finding ima draft_assertion_id i corpus_assertion_id

**Novi pristup:**
- **Finding ima assertion1_id i assertion2_id**
- Obe asercije su iz istog Assertion entiteta
- Može biti: draft vs corpus, draft vs draft, corpus vs corpus

**Prednosti:**
- Fleksibilnije (može detektovati konflikte unutar drafta)
- Može detektovati konflikte unutar korpusa
- Jednostavniji model

**Primer:**
```json
{
  "id": "find555",
  "review_id": "review123",
  "assertion1_id": "assert_draft_001",  // is_draft=true
  "assertion2_id": "assert_corpus_042", // is_draft=false
  "conflict_type": "contradictory_deadline",
  "severity": "high",
  "message": "Konflikt rokova..."
}
```

---

### 6. Resolution (Kombinovano Rešenje i Odluka)

**Novi entitet:**
- **Resolution** - Kombinuje rešenje i odluku korisnika za finding

**Atributi:**
- Status: "pending", "accepted", "rejected", "modified", "ignored"
- Action: "accept_draft", "accept_corpus", "modify_draft", "modify_corpus", "ignore"
- Reason za odluku
- Notes od korisnika
- Modified text (ako je modify)
- Tracking ko je rešio i kada

**Prednosti:**
- Jednostavniji model (jedan entitet umesto dva)
- Sve informacije na jednom mestu
- Lakše query-ovanje

**Primer:**
```json
{
  "id": "res777",
  "review_id": "review123",
  "finding_id": "find555",
  "status": "accepted",
  "action": "modify_draft",
  "reason": "Rok treba biti do 15. umesto do 20. u skladu sa Zakonom o radu",
  "notes": "Uskladiti sa Zakonom o radu. Promeniti rok sa 20. na 15. u mesecu.",
  "modified_text": "Poslodavac je dužan da zaposlenom isplati zaradu najkasnije do 15. u mesecu",
  "user_id": "user999",
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:05:00Z"
}
```

---

## Refaktorisani Entiteti

### 1. Domain (Domen)

**Atributi:**
- `id` (UUID)
- `name` (string) - "Radno pravo"
- `description` (text)
- `default_conflict_set_id` (UUID, nullable) - Default set pravila
- `created_at` (datetime)

**Odnosi:**
- **N:M sa Ontology** - Koristi više ontologija
- **1:N sa Corpus** - Ima više korpusa
- **N:M sa ConflictSet** - Koristi više setova pravila (via domain_conflict_sets)
- **N:1 sa ConflictSet** (default) - Ima default set

---

### 2. Ontology (Ontologija)

**Atributi:**
- `id` (UUID)
- `name` (string) - "Radno pravo - Osnovna"
- `terms` (JSON) - Termini i sinonimi
- `concepts` (JSON) - Hijerarhija koncepata
- `rules` (JSON) - Pravila za ekstrakciju
- `version` (int)
- `created_at` (datetime)

**Odnosi:**
- **N:M sa Domain** - Koristi se u više domena
- **N:M sa Corpus** - Koristi se u više korpusa

**Join tabele:**
- `domain_ontologies` (domain_id, ontology_id)
- `corpus_ontologies` (corpus_id, ontology_id)

---

### 3. Corpus (Korpus)

**Atributi:**
- `id` (UUID)
- `name` (string)
- `domain_id` (UUID)
- `description` (text)
- `status` (enum)
- `documents_count` (int)
- `assertions_count` (int)
- `created_at` (datetime)

**Odnosi:**
- **N:1 sa Domain**
- **N:M sa Ontology**
- **1:N sa Document**

---

### 4. Document (Dokument) - UNIVERZALAN

**Atributi:**
- `id` (UUID)
- `corpus_id` (UUID, nullable) - Null ako je draft koji nije u korpusu
- `filename` (string)
- `title` (string)
- `document_type` (enum) - "law", "regulation", "decree", "rulebook"
- `is_draft` (boolean) - **KEY: True ako je draft, False ako je corpus**
- `content` (text)
- `metadata` (JSON)
- `created_at` (datetime)

**Odnosi:**
- **N:1 sa Corpus** (optional)
- **1:N sa LegalUnit**
- **1:N sa DraftReview** (ako je draft)

**Primer:**
```json
// Corpus document
{
  "id": "doc123",
  "corpus_id": "corpus789",
  "title": "Zakon o radu",
  "is_draft": false,
  "content": "..."
}

// Draft document
{
  "id": "doc456",
  "corpus_id": null,
  "title": "Pravilnik o radu - Nacrt",
  "is_draft": true,
  "content": "..."
}
```

---

### 5. LegalUnit (Pravna Jedinica) - UNIVERZALAN

**Atributi:**
- `id` (UUID)
- `document_id` (UUID)
- `type` (enum) - "article", "paragraph", "item", "subitem"
- `number` (string)
- `text` (text)
- `parent_id` (UUID, nullable)
- `hierarchy_path` (string)

**Odnosi:**
- **N:1 sa Document**
- **1:N sa Assertion**
- **1:N sa LegalUnit** (self-reference)

**Napomena:** Isti entitet za corpus i draft dokumente!

---

### 6. Assertion (Asercija) - UNIVERZALAN

**Atributi:**
- `id` (UUID)
- `legal_unit_id` (UUID)
- `document_id` (UUID)
- `corpus_id` (UUID, nullable) - Null ako je iz drafta
- `assertion_type` (enum)
- `subject` (string)
- `action` (string)
- `object` (string, nullable)
- `condition` (string, nullable)
- `deadline` (string, nullable)
- `penalty` (string, nullable)
- `text` (text)
- `confidence` (float)
- `is_draft` (boolean) - **Computed: document.is_draft**

**Odnosi:**
- **N:1 sa LegalUnit**
- **N:1 sa Document**
- **N:1 sa Corpus** (optional)
- **1:1 sa Embedding**
- **N:M sa Finding** (kao assertion1 ili assertion2)

**Napomena:** Isti entitet za corpus i draft asercije!

**Query primeri:**
```sql
-- Sve corpus asercije
SELECT * FROM assertions WHERE is_draft = false;

-- Sve draft asercije
SELECT * FROM assertions WHERE is_draft = true;

-- Asercije iz specifičnog drafta
SELECT * FROM assertions WHERE document_id = 'doc456';
```

---

### 7. Embedding (Vektor)

**Atributi:**
- `id` (UUID)
- `assertion_id` (UUID)
- `vector` (array[float])
- `model` (string)
- `dimensions` (int)
- `created_at` (datetime)

**Odnosi:**
- **1:1 sa Assertion**

**Napomena:** Embeddings se generišu i za corpus i za draft asercije!

---

### 8. ConflictSet (Skup Pravila)

**Atributi:**
- `id` (UUID)
- `domain_id` (UUID)
- `name` (string) - "Radno pravo - Standard"
- `description` (text)
- `version` (int)
- `is_default` (boolean)
- `created_at` (datetime)

**Odnosi:**
- **N:1 sa Domain**
- **1:N sa ConflictRule**
- **1:N sa DraftReview** (koristi se u review-ima)

**Primer:**
```json
{
  "id": "set111",
  "domain_id": "domain222",
  "name": "Radno pravo - Standard",
  "description": "Standardni set pravila za radno pravo",
  "version": 1,
  "is_default": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### 9. ConflictRule (Pravilo Konflikta)

**Atributi:**
- `id` (UUID)
- `conflict_set_id` (UUID)
- `type` (string) - "contradictory_obligation"
- `category` (enum) - "normative", "temporal", etc.
- `name` (string)
- `description` (text)
- `detection_logic` (JSON)
- `severity` (enum)
- `enabled` (boolean)
- `version` (int)

**Odnosi:**
- **N:1 sa ConflictSet**
- **1:N sa Finding** (koristi se za detekciju)

---

### 10. DraftReview (Sesija Analize)

**Atributi:**
- `id` (UUID)
- `name` (string)
- `draft_document_id` (UUID) - Document sa is_draft=true
- `corpus_id` (UUID)
- `conflict_set_id` (UUID) - Koji set pravila koristiti
- `status` (enum) - "pending", "processing", "completed", "error"
- `findings_count` (int)
- `created_at` (datetime)
- `completed_at` (datetime, nullable)
- `created_by` (UUID) - User koji je pokrenuo

**Odnosi:**
- **N:1 sa Document** (draft)
- **N:1 sa Corpus**
- **N:1 sa ConflictSet**
- **1:N sa Finding**
- **1:N sa Resolution**

**Primer:**
```json
{
  "id": "review123",
  "name": "Pravilnik o radu - Analiza 2024-01-20",
  "draft_document_id": "doc456",
  "corpus_id": "corpus789",
  "conflict_set_id": "set111",
  "status": "completed",
  "findings_count": 8,
  "created_at": "2024-01-20T09:00:00Z",
  "completed_at": "2024-01-20T09:05:23Z",
  "created_by": "user999"
}
```

---

### 11. Finding (Nalaz)

**Atributi:**
- `id` (UUID)
- `draft_review_id` (UUID)
- `assertion1_id` (UUID) - Prva asercija (obično draft)
- `assertion2_id` (UUID) - Druga asercija (obično corpus)
- `conflict_rule_id` (UUID) - Pravilo koje je detektovalo
- `conflict_type` (string)
- `category` (enum)
- `severity` (enum)
- `title` (string)
- `message` (text)
- `location1` (string) - Lokacija u dokumentu 1
- `location2` (string) - Lokacija u dokumentu 2
- `suggestion` (text, nullable)
- `created_at` (datetime)

**Odnosi:**
- **N:1 sa DraftReview**
- **N:1 sa Assertion** (assertion1)
- **N:1 sa Assertion** (assertion2)
- **N:1 sa ConflictRule**
- **1:N sa Decision**

**Primer:**
```json
{
  "id": "find555",
  "draft_review_id": "review123",
  "assertion1_id": "assert_draft_001",
  "assertion2_id": "assert_corpus_042",
  "conflict_rule_id": "rule666",
  "conflict_type": "contradictory_deadline",
  "category": "temporal",
  "severity": "high",
  "title": "Konflikt rokova za isplatu zarade",
  "message": "Draft propisuje rok do 20. u mesecu, dok Zakon o radu propisuje rok do 15. u mesecu",
  "location1": "Član 12, stav 1",
  "location2": "Zakon o radu, Član 108",
  "suggestion": "Uskladiti rok sa Zakonom o radu (do 15. u mesecu)",
  "created_at": "2024-01-20T09:05:15Z"
}
```

---

### 12. Resolution (Rešenje)

**Atributi:**
- `id` (UUID)
- `draft_review_id` (UUID)
- `finding_id` (UUID)
- `status` (enum) - "pending", "accepted", "rejected", "modified", "ignored"
- `notes` (text)
- `user_id` (UUID)
- `created_at` (datetime)
- `updated_at` (datetime)

**Odnosi:**
- **N:1 sa DraftReview**
- **N:1 sa Finding**

**Primer:**
```json
{
  "id": "res777",
  "draft_review_id": "review123",
  "finding_id": "find555",
  "status": "accepted",
  "notes": "Uskladiti sa Zakonom o radu. Promeniti rok sa 20. na 15. u mesecu.",
  "user_id": "user999",
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z"
}
```

---

### 13. Decision (Odluka)

**Atributi:**
- `id` (UUID)
- `finding_id` (UUID)
- `action` (enum) - "accept_draft", "accept_corpus", "modify_draft", "modify_corpus", "ignore"
- `reason` (text)
- `modified_text` (text, nullable) - Novi tekst ako je modify
- `user_id` (UUID)
- `timestamp` (datetime)

**Odnosi:**
- **N:1 sa Finding**

**Primer:**
```json
{
  "id": "dec888",
  "finding_id": "find555",
  "action": "modify_draft",
  "reason": "Rok treba biti do 15. umesto do 20. u skladu sa Zakonom o radu",
  "modified_text": "Poslodavac je dužan da zaposlenom isplati zaradu najkasnije do 15. u mesecu",
  "user_id": "user999",
  "timestamp": "2024-01-20T10:05:00Z"
}
```

---

## Relationships Summary (V2)

| Odnos | Tip | Opis |
|-------|-----|------|
| Domain ↔ Ontology | N:M | Domen koristi više ontologija |
| Corpus ↔ Ontology | N:M | Korpus koristi više ontologija |
| Domain → Corpus | 1:N | Domen ima više korpusa |
| Domain → ConflictSet | 1:N | Domen ima više setova pravila |
| ConflictSet → ConflictRule | 1:N | Set ima više pravila |
| Corpus → Document | 1:N | Korpus ima više dokumenata |
| Document → LegalUnit | 1:N | Dokument ima više jedinica |
| LegalUnit → Assertion | 1:N | Jedinica ima više asercija |
| Assertion → Embedding | 1:1 | Asercija ima embedding |
| DraftReview → Document | N:1 | Review analizira draft |
| DraftReview → Corpus | N:1 | Review koristi korpus |
| DraftReview → ConflictSet | N:1 | Review koristi set pravila |
| DraftReview → Finding | 1:N | Review proizvodi findings |
| Finding → Assertion | N:1 | Finding povezuje 2 asercije |
| Finding → ConflictRule | N:1 | Finding detektovan pravilom |
| DraftReview → Resolution | 1:N | Review ima rešenja |
| Finding → Decision | 1:N | Finding ima odluke |

---

## Data Flow Examples (V2)

### 1. Import Korpusa

```
1. User uploads documents
   ↓
2. Create Corpus entity
   ↓
3. For each file:
   a. Create Document entity (is_draft=false)
   b. Parse → Create LegalUnit entities
   c. Extract → Create Assertion entities (is_draft=false)
   d. Generate → Create Embedding entities
   ↓
4. Auto-learn → Create/Update Ontology
   ↓
5. Link Ontology to Corpus (corpus_ontologies table)
   ↓
6. Index → Store in Qdrant
   ↓
7. Update Corpus status = "ready"
```

---

### 2. Draft Review

```
1. User uploads draft document
   ↓
2. Create Document entity (is_draft=true, corpus_id=null)
   ↓
3. Parse draft:
   a. Create LegalUnit entities
   b. Extract → Create Assertion entities (is_draft=true)
   c. Generate → Create Embedding entities
   ↓
4. User selects Corpus and ConflictSet
   ↓
5. Create DraftReview entity
   ↓
6. For each draft Assertion:
   a. Find similar corpus Assertions (via embeddings)
   b. Apply ConflictRules from ConflictSet
   c. If conflict detected → Create Finding entity
   ↓
7. Update DraftReview status = "completed"
   ↓
8. User reviews Findings
   ↓
9. For each Finding:
   a. User creates Decision
   b. System creates Resolution
   ↓
10. Generate report
```

---

### 3. Conflict Detection Logic

```sql
-- Pseudo-SQL za conflict detection

-- 1. Dobavi sve draft asercije
SELECT * FROM assertions 
WHERE document_id = :draft_document_id 
  AND is_draft = true;

-- 2. Za svaku draft aserciju, nađi slične corpus asercije
SELECT a2.* 
FROM assertions a2
JOIN embeddings e1 ON e1.assertion_id = :draft_assertion_id
JOIN embeddings e2 ON e2.assertion_id = a2.id
WHERE a2.is_draft = false
  AND a2.corpus_id = :corpus_id
  AND vector_similarity(e1.vector, e2.vector) > 0.25
ORDER BY vector_similarity(e1.vector, e2.vector) DESC
LIMIT 10;

-- 3. Primeni pravila iz ConflictSet
SELECT cr.* 
FROM conflict_rules cr
WHERE cr.conflict_set_id = :conflict_set_id
  AND cr.enabled = true;

-- 4. Za svako pravilo, proveri da li postoji konflikt
-- (logika zavisi od pravila)

-- 5. Ako postoji konflikt, kreiraj Finding
INSERT INTO findings (
  draft_review_id,
  assertion1_id,  -- draft
  assertion2_id,  -- corpus
  conflict_rule_id,
  conflict_type,
  severity,
  ...
) VALUES (...);
```

---

## Storage Mapping (V2)

### SQLite Tables

| Entity | Table | Notes |
|--------|-------|-------|
| Domain | `domains` | |
| Ontology | `ontologies` | |
| Corpus | `corpora` | |
| Document | `documents` | **Unified: corpus + draft** |
| LegalUnit | `legal_units` | **Unified: corpus + draft** |
| Assertion | `assertions` | **Unified: corpus + draft** |
| Embedding | `embeddings` | |
| ConflictSet | `conflict_sets` | |
| ConflictRule | `conflict_rules` | |
| DraftReview | `draft_reviews` | |
| Finding | `findings` | |
| Resolution | `resolutions` | |
| Decision | `decisions` | |

### Join Tables

| Table | Columns | Purpose |
|-------|---------|---------|
| `domain_ontologies` | domain_id, ontology_id | N:M Domain ↔ Ontology |
| `corpus_ontologies` | corpus_id, ontology_id | N:M Corpus ↔ Ontology |
| `domain_conflict_sets` | domain_id, conflict_set_id, is_default | N:M Domain ↔ ConflictSet |

---

## Migration Strategy

### Faza 1: Dodaj Nove Kolone

```sql
-- documents tabela
ALTER TABLE documents ADD COLUMN is_draft BOOLEAN DEFAULT false;

-- assertions tabela  
ALTER TABLE assertions ADD COLUMN is_draft BOOLEAN DEFAULT false;

-- Novi entiteti
CREATE TABLE conflict_sets (...);
CREATE TABLE resolutions (...);
CREATE TABLE decisions (...);

-- Join tabele
CREATE TABLE domain_ontologies (...);
CREATE TABLE corpus_ontologies (...);
```

### Faza 2: Migracija Podataka

```sql
-- Označi sve postojeće dokumente kao corpus (ne draft)
UPDATE documents SET is_draft = false WHERE corpus_id IS NOT NULL;

-- Označi sve postojeće asercije kao corpus
UPDATE assertions SET is_draft = false WHERE corpus_id IS NOT NULL;

-- Kreiraj globalni ConflictSet
INSERT INTO conflict_sets (name, description, is_global, version)
VALUES ('Standard - Sva pravila', 'Standardni set sa svih 127 pravila', true, 1);

-- Poveži sve domene sa globalnim setom
INSERT INTO domain_conflict_sets (domain_id, conflict_set_id, is_default)
SELECT d.id, cs.id, true
FROM domains d
CROSS JOIN conflict_sets cs
WHERE cs.is_global = true;

-- Migriraj postojeća pravila u globalni ConflictSet
INSERT INTO conflict_rules (conflict_set_id, type, category, ...)
SELECT cs.id, cr.type, cr.category, ...
FROM old_conflict_rules cr
CROSS JOIN conflict_sets cs
WHERE cs.is_global = true;
```

### Faza 3: Ukloni Stare Tabele

```sql
-- Nakon što se sve migrira i testira
DROP TABLE draft_documents;
DROP TABLE draft_units;
DROP TABLE draft_assertions;
```

---

## API Endpoints (V2)

### Document Management (Unified)

```
POST   /api/v1/documents                  → Create Document (corpus or draft)
GET    /api/v1/documents/{id}             → Get Document
PUT    /api/v1/documents/{id}             → Update Document
DELETE /api/v1/documents/{id}             → Delete Document

# Query params
GET    /api/v1/documents?is_draft=true    → List draft documents
GET    /api/v1/documents?corpus_id={id}   → List corpus documents
```

### Draft Review

```
POST   /api/v1/draft-reviews               → Create DraftReview
GET    /api/v1/draft-reviews                → List DraftReviews
GET    /api/v1/draft-reviews/{id}           → Get DraftReview
GET    /api/v1/draft-reviews/{id}/findings  → Get Findings
POST   /api/v1/draft-reviews/{id}/resolutions → Create Resolution
```

### Findings & Decisions

```
GET    /api/v1/findings/{id}               → Get Finding
POST   /api/v1/findings/{id}/decisions     → Create Decision
GET    /api/v1/findings/{id}/decisions     → List Decisions
```

### Conflict Management

```
GET    /api/v1/conflict-sets               → List ConflictSets
GET    /api/v1/conflict-sets/{id}          → Get ConflictSet
POST   /api/v1/conflict-sets               → Create ConflictSet
GET    /api/v1/conflict-sets/{id}/rules    → List Rules in Set
PUT    /api/v1/conflict-rules/{id}         → Update Rule
```

---

## Prednosti V2 Modela

### 1. Manje Duplikacije
- Jedan Document entitet umesto 2
- Jedan LegalUnit entitet umesto 2
- Jedan Assertion entitet umesto 2
- **~40% manje koda**

### 2. Fleksibilniji Conflict Detection
- Može detektovati konflikte draft vs corpus
- Može detektovati konflikte draft vs draft
- Može detektovati konflikte corpus vs corpus
- **Više mogućnosti analize**

### 3. Reusable Ontology
- Ontologija se deli između domena i korpusa
- Lakše održavanje
- Konzistentnija ekstrakcija
- **Manje redundancije**

### 4. Konfigurabilan Conflict Detection
- ConflictSet omogućava različite setove pravila
- A/B testiranje pravila
- Domain-specific pravila
- **Veća fleksibilnost**

### 5. Tracking Decisions
- Resolution i Decision entiteti
- Istorija odluka
- Audit trail
- **Bolja accountability**

### 6. Lakša Migracija Draft → Corpus
```sql
-- Draft postaje corpus document
UPDATE documents 
SET is_draft = false, corpus_id = :corpus_id
WHERE id = :draft_id;

-- Sve asercije automatski postaju corpus asercije
UPDATE assertions
SET is_draft = false, corpus_id = :corpus_id
WHERE document_id = :draft_id;
```

---

## Zaključak

**V2 Model je:**
- ✅ Logičniji (manje duplikacije)
- ✅ Fleksibilniji (više mogućnosti)
- ✅ Lakši za održavanje
- ✅ Skalabilniji
- ✅ Bolje organizovan

**Ključne izmene:**
1. 🔄 **Unified Document/LegalUnit/Assertion** - is_draft flag
2. 🔗 **Ontology N:M sa Domain** - Reusable ontologije
3. 📋 **ConflictSet + ConflictRule** - Konfigurabilan detection
4. 🎯 **Finding povezuje 2 Assertion** - Fleksibilnije poređenje
5. ✅ **Resolution + Decision** - Tracking odluka

**Preporuka:** Implementiraj V2 model!