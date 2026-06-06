# ZAIKON - Domain Model & Component Architecture

## Pregled

Ovaj dokument definiše sve ključne entitete (domain objects) u ZAIKON sistemu, njihove odnose, i kako međusobno komuniciraju.

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ZAIKON DOMAIN MODEL                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Domain     │ 1     * │   Corpus     │ 1     * │  Document    │
│              ├─────────┤              ├─────────┤              │
│ - id         │ contains│ - id         │ contains│ - id         │
│ - name       │         │ - name       │         │ - filename   │
│ - desc       │         │ - domain_id  │         │ - corpus_id  │
└──────────────┘         │ - status     │         │ - content    │
                         │ - created_at │         │ - metadata   │
                         └──────┬───────┘         └──────┬───────┘
                                │                        │
                                │ 1                      │ 1
                                │                        │
                                │ *                      │ *
                         ┌──────┴───────┐         ┌─────┴────────┐
                         │  Ontology    │         │ LegalUnit    │
                         │              │         │              │
                         │ - id         │         │ - id         │
                         │ - corpus_id  │         │ - doc_id     │
                         │ - terms      │         │ - type       │
                         │ - rules      │         │ - number     │
                         └──────────────┘         │ - text       │
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
                                                  │ - type       │
                                                  │ - subject    │
                                                  │ - action     │
                                                  │ - object     │
                                                  │ - deadline   │
                                                  └──────┬───────┘
                                                         │
                                                         │ *
                                                         │
                                                         │ *
┌──────────────┐         ┌──────────────┐         ┌────┴─────────┐
│ DraftReview  │ 1     * │   Finding    │ *     * │  Conflict    │
│              ├─────────┤              ├─────────┤              │
│ - id         │ produces│ - id         │ detects │ - type       │
│ - draft_text │         │ - review_id  │         │ - category   │
│ - corpus_id  │         │ - type       │         │ - severity   │
│ - status     │         │ - severity   │         │ - rule_id    │
│ - created_at │         │ - message    │         └──────────────┘
└──────┬───────┘         │ - location   │
       │                 │ - suggestion │
       │ 1               └──────────────┘
       │
       │ *
┌──────┴───────┐
│ DraftUnit    │
│              │
│ - id         │
│ - review_id  │
│ - type       │
│ - number     │
│ - text       │
└──────┬───────┘
       │
       │ 1
       │
       │ *
┌──────┴───────┐
│DraftAssertion│
│              │
│ - id         │
│ - unit_id    │
│ - type       │
│ - subject    │
│ - action     │
│ - object     │
│ - deadline   │
└──────────────┘


┌──────────────┐         ┌──────────────┐
│ ConflictRule │ 1     * │   Conflict   │
│              ├─────────┤              │
│ - id         │ defines │ - type       │
│ - type       │         │ - category   │
│ - category   │         │ - severity   │
│ - logic      │         │ - rule_id    │
│ - severity   │         └──────────────┘
└──────────────┘


┌──────────────┐         ┌──────────────┐
│   Embedding  │ 1     1 │  Assertion   │
│              ├─────────┤              │
│ - id         │ for     │ - id         │
│ - vector     │         │ - text       │
│ - model      │         └──────────────┘
│ - dimensions │
└──────────────┘
```

---

## 1. Core Entities

### 1.1 Domain (Domen)

**Opis:** Predstavlja pravnu oblast ili domenu (npr. Radno pravo, Šumarstvo, Zdravstvo).

**Atributi:**
- `id` (UUID) - Jedinstveni identifikator
- `name` (string) - Naziv domene
- `description` (string) - Opis domene
- `created_at` (datetime) - Vreme kreiranja

**Odnosi:**
- **1:N sa Corpus** - Jedan domen može imati više korpusa

**Primer:**
```json
{
  "id": "d1a2b3c4-...",
  "name": "Radno pravo",
  "description": "Zakoni i propisi koji regulišu radne odnose u Republici Srbiji",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Upotreba:**
- Organizacija korpusa po pravnim oblastima
- Filtriranje i pretraga po domenima
- Specijalizovana ontologija po domenu

---

### 1.2 Corpus (Korpus)

**Opis:** Kolekcija pravnih dokumenata iz određene domene koja služi kao referentna baza za analizu.

**Atributi:**
- `id` (UUID) - Jedinstveni identifikator
- `name` (string) - Naziv korpusa
- `domain_id` (UUID) - Referenca na domen
- `description` (string) - Opis korpusa
- `status` (enum) - Status: "importing", "ready", "error"
- `documents_count` (int) - Broj dokumenata
- `assertions_count` (int) - Broj ekstrahovanih asercija
- `created_at` (datetime) - Vreme kreiranja
- `updated_at` (datetime) - Vreme poslednje izmene

**Odnosi:**
- **N:1 sa Domain** - Pripada jednom domenu
- **1:N sa Document** - Sadrži više dokumenata
- **1:1 sa Ontology** - Ima svoju ontologiju
- **1:N sa DraftReview** - Koristi se u više draft review-a

**Primer:**
```json
{
  "id": "8a42b6e2-...",
  "name": "Pilot Radni Odnosi",
  "domain_id": "d1a2b3c4-...",
  "description": "Pilot korpus sa zakonima o radnim odnosima",
  "status": "ready",
  "documents_count": 15,
  "assertions_count": 342,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:45:00Z"
}
```

**Upotreba:**
- Referentna baza za conflict detection
- Izvor za semantic search
- Osnova za ontologiju

---

### 1.3 Document (Dokument)

**Opis:** Pojedinačni pravni dokument (zakon, pravilnik, uredba) unutar korpusa.

**Atributi:**
- `id` (UUID) - Jedinstveni identifikator
- `corpus_id` (UUID) - Referenca na korpus
- `filename` (string) - Ime fajla
- `title` (string) - Naslov dokumenta
- `document_type` (enum) - Tip: "law", "regulation", "decree", "rulebook"
- `content` (text) - Pun tekst dokumenta
- `metadata` (JSON) - Dodatni metapodaci
- `created_at` (datetime) - Vreme kreiranja

**Odnosi:**
- **N:1 sa Corpus** - Pripada jednom korpusu
- **1:N sa LegalUnit** - Sadrži više pravnih jedinica

**Primer:**
```json
{
  "id": "doc123-...",
  "corpus_id": "8a42b6e2-...",
  "filename": "zakon_o_radu.txt",
  "title": "Zakon o radu",
  "document_type": "law",
  "content": "Član 1\nOvim zakonom uređuju se...",
  "metadata": {
    "official_gazette": "Sl. glasnik RS, br. 24/2005",
    "effective_date": "2005-06-01"
  },
  "created_at": "2024-01-15T10:35:00Z"
}
```

**Upotreba:**
- Izvor teksta za parsiranje
- Referenca u findings
- Metadata za kontekst

---

### 1.4 LegalUnit (Pravna Jedinica)

**Opis:** Strukturna jedinica pravnog dokumenta (član, stav, tačka, alineja).

**Atributi:**
- `id` (UUID) - Jedinstveni identifikator
- `document_id` (UUID) - Referenca na dokument
- `type` (enum) - Tip: "article", "paragraph", "item", "subitem"
- `number` (string) - Broj jedinice (npr. "1", "2a", "3.1")
- `text` (text) - Tekst jedinice
- `parent_id` (UUID, nullable) - Referenca na parent jedinicu
- `hierarchy_path` (string) - Putanja u hijerarhiji (npr. "1.2.a")

**Odnosi:**
- **N:1 sa Document** - Pripada jednom dokumentu
- **1:N sa Assertion** - Sadrži više asercija
- **1:N sa LegalUnit** (self-reference) - Hijerarhijska struktura

**Primer:**
```json
{
  "id": "unit456-...",
  "document_id": "doc123-...",
  "type": "article",
  "number": "15",
  "text": "Poslodavac je dužan da zaposlenom isplati zaradu...",
  "parent_id": null,
  "hierarchy_path": "15"
}
```

**Upotreba:**
- Strukturno parsiranje dokumenata
- Precizna lokacija asercija
- Hijerarhijska navigacija

---

### 1.5 Assertion (Asercija)

**Opis:** Normativna tvrdnja ekstraktovana iz pravne jedinice (obaveza, zabrana, dozvola, rok).

**Atributi:**
- `id` (UUID) - Jedinstveni identifikator
- `legal_unit_id` (UUID) - Referenca na pravnu jedinicu
- `corpus_id` (UUID) - Referenca na korpus
- `document_id` (UUID) - Referenca na dokument
- `assertion_type` (enum) - Tip: "obligation", "prohibition", "permission", "deadline", "definition"
- `subject` (string) - Subjekat (ko)
- `action` (string) - Akcija (šta)
- `object` (string, nullable) - Objekat (nad čim)
- `condition` (string, nullable) - Uslov (kada/ako)
- `deadline` (string, nullable) - Rok (do kada)
- `penalty` (string, nullable) - Kazna (šta ako ne)
- `text` (text) - Originalni tekst
- `confidence` (float) - Pouzdanost ekstrakcije (0-1)

**Odnosi:**
- **N:1 sa LegalUnit** - Ekstraktovana iz pravne jedinice
- **N:1 sa Corpus** - Pripada korpusu
- **N:1 sa Document** - Iz dokumenta
- **1:1 sa Embedding** - Ima svoj embedding vektor
- **N:M sa Conflict** - Učestvuje u konfliktima

**Primer:**
```json
{
  "id": "assert789-...",
  "legal_unit_id": "unit456-...",
  "corpus_id": "8a42b6e2-...",
  "document_id": "doc123-...",
  "assertion_type": "obligation",
  "subject": "poslodavac",
  "action": "isplatiti zaradu",
  "object": "zaposlenom",
  "condition": null,
  "deadline": "najkasnije do 15. u mesecu",
  "penalty": null,
  "text": "Poslodavac je dužan da zaposlenom isplati zaradu najkasnije do 15. u mesecu",
  "confidence": 0.92
}
```

**Upotreba:**
- Osnova za conflict detection
- Semantic search
- Ontology extraction

---

### 1.6 Ontology (Ontologija)

**Opis:** Skup termina, koncepata i pravila specifičnih za domen/korpus.

**Atributi:**
- `id` (UUID) - Jedinstveni identifikator
- `corpus_id` (UUID) - Referenca na korpus
- `terms` (JSON) - Lista termina sa sinonimima
- `concepts` (JSON) - Hijerarhija koncepata
- `rules` (JSON) - Pravila za ekstrakciju
- `version` (int) - Verzija ontologije
- `auto_learned` (boolean) - Da li je auto-generisana
- `created_at` (datetime) - Vreme kreiranja
- `updated_at` (datetime) - Vreme poslednje izmene

**Odnosi:**
- **1:1 sa Corpus** - Pripada jednom korpusu

**Primer:**
```json
{
  "id": "onto111-...",
  "corpus_id": "8a42b6e2-...",
  "terms": {
    "zaposleni": ["radnik", "službenik", "lice u radnom odnosu"],
    "poslodavac": ["pravno lice", "preduzeće", "poslodavac"],
    "zarada": ["plata", "nadoknada", "primanja"]
  },
  "concepts": {
    "radni_odnos": {
      "parent": null,
      "children": ["zasnivanje", "prestanak", "prava", "obaveze"]
    }
  },
  "rules": {
    "obligation_patterns": [
      "dužan je da",
      "mora da",
      "obavezan je"
    ]
  },
  "version": 3,
  "auto_learned": true,
  "created_at": "2024-01-15T10:40:00Z",
  "updated_at": "2024-01-20T14:20:00Z"
}
```

**Upotreba:**
- Poboljšanje ekstrakcije asercija
- Semantic matching
- Auto-tuning sistema

---

### 1.7 DraftReview (Pregled Nacrta)

**Opis:** Sesija analize nacrta propisa protiv korpusa.

**Atributi:**
- `id` (UUID) - Jedinstveni identifikator
- `name` (string) - Naziv review-a
- `draft_text` (text) - Tekst nacrta
- `corpus_id` (UUID) - Referenca na korpus
- `status` (enum) - Status: "pending", "processing", "completed", "error"
- `findings_count` (int) - Broj pronađenih konflikata
- `created_at` (datetime) - Vreme kreiranja
- `completed_at` (datetime, nullable) - Vreme završetka

**Odnosi:**
- **N:1 sa Corpus** - Analizira se protiv korpusa
- **1:N sa DraftUnit** - Sadrži pravne jedinice nacrta
- **1:N sa Finding** - Proizvodi findings

**Primer:**
```json
{
  "id": "review222-...",
  "name": "Pravilnik o radu - Januar 2024",
  "draft_text": "Član 1\nOvim pravilnikom uređuje se...",
  "corpus_id": "8a42b6e2-...",
  "status": "completed",
  "findings_count": 8,
  "created_at": "2024-01-20T09:00:00Z",
  "completed_at": "2024-01-20T09:05:23Z"
}
```

**Upotreba:**
- Organizacija draft analiza
- Tracking statusa
- Istorija review-a

---

### 1.8 DraftUnit (Jedinica Nacrta)

**Opis:** Pravna jedinica iz nacrta propisa (isti koncept kao LegalUnit ali za draft).

**Atributi:**
- `id` (UUID) - Jedinstveni identifikator
- `draft_review_id` (UUID) - Referenca na draft review
- `type` (enum) - Tip: "article", "paragraph", "item", "subitem"
- `number` (string) - Broj jedinice
- `text` (text) - Tekst jedinice
- `parent_id` (UUID, nullable) - Referenca na parent
- `hierarchy_path` (string) - Putanja u hijerarhiji

**Odnosi:**
- **N:1 sa DraftReview** - Pripada draft review-u
- **1:N sa DraftAssertion** - Sadrži asercije
- **1:N sa DraftUnit** (self-reference) - Hijerarhija

**Primer:**
```json
{
  "id": "dunit333-...",
  "draft_review_id": "review222-...",
  "type": "article",
  "number": "5",
  "text": "Zaposleni ima pravo na godišnji odmor...",
  "parent_id": null,
  "hierarchy_path": "5"
}
```

**Upotreba:**
- Strukturno parsiranje nacrta
- Lokacija konflikata
- Navigacija kroz draft

---

### 1.9 DraftAssertion (Asercija Nacrta)

**Opis:** Normativna tvrdnja ekstraktovana iz nacrta (isti koncept kao Assertion ali za draft).

**Atributi:**
- `id` (UUID) - Jedinstveni identifikator
- `draft_unit_id` (UUID) - Referenca na draft unit
- `draft_review_id` (UUID) - Referenca na draft review
- `assertion_type` (enum) - Tip asercije
- `subject` (string) - Subjekat
- `action` (string) - Akcija
- `object` (string, nullable) - Objekat
- `condition` (string, nullable) - Uslov
- `deadline` (string, nullable) - Rok
- `penalty` (string, nullable) - Kazna
- `text` (text) - Originalni tekst
- `confidence` (float) - Pouzdanost

**Odnosi:**
- **N:1 sa DraftUnit** - Iz draft jedinice
- **N:1 sa DraftReview** - Pripada review-u
- **N:M sa Finding** - Učestvuje u findings

**Primer:**
```json
{
  "id": "dassert444-...",
  "draft_unit_id": "dunit333-...",
  "draft_review_id": "review222-...",
  "assertion_type": "permission",
  "subject": "zaposleni",
  "action": "koristiti godišnji odmor",
  "object": null,
  "condition": null,
  "deadline": "u periodu od 1. juna do 30. septembra",
  "penalty": null,
  "text": "Zaposleni ima pravo na godišnji odmor u periodu od 1. juna do 30. septembra",
  "confidence": 0.88
}
```

**Upotreba:**
- Poređenje sa corpus assertions
- Conflict detection
- Finding generation

---

### 1.10 Finding (Nalaz)

**Opis:** Detektovani konflikt ili problem između nacrta i korpusa.

**Atributi:**
- `id` (UUID) - Jedinstveni identifikator
- `draft_review_id` (UUID) - Referenca na draft review
- `conflict_type` (string) - Tip konflikta (npr. "contradictory_obligation")
- `category` (enum) - Kategorija: "normative", "temporal", "hierarchical", etc.
- `severity` (enum) - Ozbiljnost: "critical", "high", "medium", "low"
- `title` (string) - Kratak naslov
- `message` (text) - Detaljan opis problema
- `draft_location` (string) - Lokacija u draftu (npr. "Član 5, stav 2")
- `corpus_location` (string) - Lokacija u korpusu
- `draft_assertion_id` (UUID) - Referenca na draft aserciju
- `corpus_assertion_id` (UUID) - Referenca na corpus aserciju
- `suggestion` (text, nullable) - Predlog rešenja
- `created_at` (datetime) - Vreme detekcije

**Odnosi:**
- **N:1 sa DraftReview** - Pripada review-u
- **N:1 sa DraftAssertion** - Odnosi se na draft aserciju
- **N:1 sa Assertion** - Odnosi se na corpus aserciju
- **N:1 sa ConflictRule** - Detektovan pomoću pravila

**Primer:**
```json
{
  "id": "find555-...",
  "draft_review_id": "review222-...",
  "conflict_type": "contradictory_deadline",
  "category": "temporal",
  "severity": "high",
  "title": "Konflikt rokova za isplatu zarade",
  "message": "Nacrt propisuje rok do 20. u mesecu, dok Zakon o radu propisuje rok do 15. u mesecu",
  "draft_location": "Član 12, stav 1",
  "corpus_location": "Zakon o radu, Član 108",
  "draft_assertion_id": "dassert444-...",
  "corpus_assertion_id": "assert789-...",
  "suggestion": "Uskladiti rok sa Zakonom o radu (do 15. u mesecu)",
  "created_at": "2024-01-20T09:05:15Z"
}
```

**Upotreba:**
- Prikaz konflikata korisniku
- Generisanje izveštaja
- Tracking rešenih problema

---

### 1.11 ConflictRule (Pravilo Konflikta)

**Opis:** Definicija pravila za detekciju određenog tipa konflikta.

**Atributi:**
- `id` (UUID) - Jedinstveni identifikator
- `type` (string) - Tip konflikta (npr. "contradictory_obligation")
- `category` (enum) - Kategorija konflikta
- `name` (string) - Naziv pravila
- `description` (text) - Opis pravila
- `detection_logic` (JSON) - Logika detekcije
- `severity` (enum) - Podrazumevana ozbiljnost
- `enabled` (boolean) - Da li je pravilo aktivno
- `version` (int) - Verzija pravila

**Odnosi:**
- **1:N sa Finding** - Koristi se za detekciju findings

**Primer:**
```json
{
  "id": "rule666-...",
  "type": "contradictory_deadline",
  "category": "temporal",
  "name": "Konfliktni rokovi",
  "description": "Detektuje kada draft i corpus imaju različite rokove za istu obavezu",
  "detection_logic": {
    "require_match": ["subject", "action"],
    "require_difference": ["deadline"],
    "similarity_threshold": 0.8
  },
  "severity": "high",
  "enabled": true,
  "version": 2
}
```

**Upotreba:**
- Konfiguracija conflict detection
- Tuning pravila
- Verzionisanje logike

---

### 1.12 Embedding (Vektor)

**Opis:** Vektorska reprezentacija asercije za semantic search.

**Atributi:**
- `id` (UUID) - Jedinstveni identifikator
- `assertion_id` (UUID) - Referenca na aserciju
- `vector` (array[float]) - Embedding vektor (1024 dimenzije)
- `model` (string) - Model korišćen za generisanje (npr. "BAAI/bge-m3")
- `dimensions` (int) - Broj dimenzija (1024)
- `created_at` (datetime) - Vreme generisanja

**Odnosi:**
- **1:1 sa Assertion** - Vektor za aserciju

**Primer:**
```json
{
  "id": "emb777-...",
  "assertion_id": "assert789-...",
  "vector": [0.123, -0.456, 0.789, ...],  // 1024 dimenzije
  "model": "BAAI/bge-m3",
  "dimensions": 1024,
  "created_at": "2024-01-15T10:45:00Z"
}
```

**Upotreba:**
- Semantic search u Qdrant
- Similarity matching
- Candidate retrieval

---

## 2. Relationships Summary

### Kardinalnosti

| Odnos | Tip | Opis |
|-------|-----|------|
| Domain → Corpus | 1:N | Jedan domen ima više korpusa |
| Corpus → Document | 1:N | Jedan korpus ima više dokumenata |
| Document → LegalUnit | 1:N | Jedan dokument ima više pravnih jedinica |
| LegalUnit → Assertion | 1:N | Jedna jedinica ima više asercija |
| Corpus → Ontology | 1:1 | Jedan korpus ima jednu ontologiju |
| Assertion → Embedding | 1:1 | Jedna asercija ima jedan embedding |
| DraftReview → DraftUnit | 1:N | Jedan review ima više draft jedinica |
| DraftUnit → DraftAssertion | 1:N | Jedna draft jedinica ima više asercija |
| DraftReview → Finding | 1:N | Jedan review proizvodi više findings |
| ConflictRule → Finding | 1:N | Jedno pravilo detektuje više findings |
| DraftAssertion ↔ Assertion | N:M | Asercije se porede za conflict detection |

---

## 3. Data Flow Examples

### 3.1 Import Korpusa

```
1. User uploads documents
   ↓
2. Create Corpus entity
   ↓
3. For each file:
   a. Create Document entity
   b. Parse → Create LegalUnit entities
   c. Extract → Create Assertion entities
   d. Generate → Create Embedding entities
   ↓
4. Auto-learn → Create/Update Ontology
   ↓
5. Index → Store in Qdrant
   ↓
6. Update Corpus status = "ready"
```

**Primer toka:**
```
Domain: "Radno pravo"
  └─ Corpus: "Pilot Radni Odnosi"
      ├─ Document: "zakon_o_radu.txt"
      │   ├─ LegalUnit: "Član 1"
      │   │   └─ Assertion: "Poslodavac je dužan..."
      │   │       └─ Embedding: [0.123, -0.456, ...]
      │   ├─ LegalUnit: "Član 2"
      │   └─ ...
      ├─ Document: "pravilnik_o_radu.txt"
      └─ Ontology: {terms: {...}, rules: {...}}
```

---

### 3.2 Draft Review

```
1. User submits draft text
   ↓
2. Create DraftReview entity
   ↓
3. Parse draft:
   a. Create DraftUnit entities
   b. Extract → Create DraftAssertion entities
   ↓
4. For each DraftAssertion:
   a. Find similar corpus assertions (via embeddings)
   b. Apply ConflictRules
   c. If conflict detected → Create Finding entity
   ↓
5. Update DraftReview status = "completed"
   ↓
6. Return findings to user
```

**Primer toka:**
```
DraftReview: "Pravilnik o radu - Januar 2024"
  ├─ DraftUnit: "Član 5"
  │   └─ DraftAssertion: "Zaposleni ima pravo na odmor..."
  │       ↓ (compare with corpus)
  │       ↓ (similarity search)
  │       ↓ (apply conflict rules)
  │       └─ Finding: "Konflikt rokova" (severity: high)
  ├─ DraftUnit: "Član 6"
  └─ ...
```

---

### 3.3 Semantic Search

```
1. User enters query: "rok za isplatu zarade"
   ↓
2. Generate query embedding
   ↓
3. Search Qdrant (vector similarity)
   ↓
4. Retrieve top N assertions
   ↓
5. Rerank results
   ↓
6. Return to user with source locations
```

**Primer toka:**
```
Query: "rok za isplatu zarade"
  ↓ embedding
  ↓ vector search
  ↓
Results:
  1. Assertion: "Poslodavac je dužan da isplati zaradu do 15. u mesecu"
     Source: Zakon o radu, Član 108
     Similarity: 0.92
  
  2. Assertion: "Zarada se isplaćuje najkasnije do kraja meseca"
     Source: Pravilnik o radu, Član 45
     Similarity: 0.85
```

---

## 4. Storage Mapping

### SQLite Tables

| Entity | Table | Primary Key |
|--------|-------|-------------|
| Domain | `domains` | `id` |
| Corpus | `corpora` | `id` |
| Document | `corpus_documents` | `id` |
| LegalUnit | `legal_units` | `id` |
| Assertion | `corpus_assertions` | `id` |
| Ontology | `ontologies` | `id` |
| DraftReview | `draft_reviews` | `id` |
| DraftUnit | `draft_units` | `id` |
| DraftAssertion | `draft_assertions` | `id` |
| Finding | `findings` | `id` |
| ConflictRule | `conflict_rules` | `id` |

### Qdrant Collections

| Entity | Collection | Vector Dimensions |
|--------|-----------|-------------------|
| Embedding | `corpus_{corpus_id}` | 1024 |

### JSON Files (Configuration)

| Entity | File | Purpose |
|--------|------|---------|
| ConflictRule | `rules/conflicts/registry.json` | Definicije pravila |
| Ontology (base) | `rules/ontology/base_sr.json` | Bazna ontologija |

---

## 5. API Endpoints Mapping

### Corpus Management

```
POST   /api/v1/corpora                    → Create Corpus
GET    /api/v1/corpora                    → List Corpora
GET    /api/v1/corpora/{id}               → Get Corpus
DELETE /api/v1/corpora/{id}               → Delete Corpus
POST   /api/v1/corpora/{id}/import-folder → Import Documents
GET    /api/v1/corpora/{id}/documents     → List Documents
GET    /api/v1/corpora/{id}/assertions    → List Assertions
```

### Draft Review

```
POST   /api/v1/draft-reviews              → Create DraftReview
GET    /api/v1/draft-reviews               → List DraftReviews
GET    /api/v1/draft-reviews/{id}          → Get DraftReview
GET    /api/v1/draft-reviews/{id}/findings → Get Findings
```

### Search

```
POST   /api/v1/search/semantic             → Semantic Search
POST   /api/v1/search/hybrid               → Hybrid Search
```

### Configuration

```
GET    /api/v1/ontology/{corpus_id}        → Get Ontology
PUT    /api/v1/ontology/{corpus_id}        → Update Ontology
GET    /api/v1/conflict-rules               → List ConflictRules
PUT    /api/v1/conflict-rules/{id}         → Update ConflictRule
```

---

## 6. Key Design Decisions

### 6.1 Zašto Odvojene Tabele za Draft i Corpus?

**Razlog:** Draft je privremeni entitet koji se često briše, dok je Corpus trajni. Odvojene tabele omogućavaju:
- Lakše brisanje draft-ova bez uticaja na corpus
- Različite optimizacije (indeksi, caching)
- Jasnu separaciju concerns

### 6.2 Zašto Embedding kao Zaseban Entitet?

**Razlog:** Embeddings su veliki (1024 float = 4KB) i često se regenerišu. Zaseban entitet omogućava:
- Regenerisanje bez brisanja asercija
- Različite modele za iste asercije
- Optimizaciju storage-a

### 6.3 Zašto Ontology kao JSON?

**Razlog:** Ontologija je fleksibilna struktura koja se često menja. JSON omogućava:
- Brze izmene bez schema migration
- Fleksibilnu strukturu
- Lako verzionisanje

### 6.4 Zašto ConflictRule kao Entitet?

**Razlog:** Pravila se često tuniraju i verzionišu. Entitet omogućava:
- Runtime konfiguraciju
- A/B testiranje pravila
- Verzionisanje i rollback

---

## 7. Scalability Considerations

### 7.1 Horizontal Scaling

**Corpus Level:**
- Svaki corpus je nezavisan
- Može se procesirati paralelno
- Može se distribuirati na više servera

**Document Level:**
- Dokumenti se procesiraju nezavisno
- Batch processing po dokumentima
- Paralelizacija moguća

### 7.2 Caching Strategy

**Entity Level:**
```
Corpus → Cache (1h)
Ontology → Cache (30min)
ConflictRules → Cache (15min)
Embeddings → Cache (permanent, invalidate on regenerate)
```

### 7.3 Database Optimization

**Indeksi:**
```sql
-- Najčešći upiti
CREATE INDEX idx_assertions_corpus ON corpus_assertions(corpus_id);
CREATE INDEX idx_findings_review ON findings(draft_review_id);
CREATE INDEX idx_findings_severity ON findings(severity);

-- Full-text search
CREATE VIRTUAL TABLE assertions_fts USING fts5(text, subject, action);
```

---

## Zaključak

Ovaj domain model definiše:
- **12 core entities** sa jasnim odgovornostima
- **Relationships** između entiteta (1:1, 1:N, N:M)
- **Data flow** kroz sistem
- **Storage mapping** (SQLite, Qdrant, JSON)
- **API endpoints** za svaki entitet
- **Design decisions** i njihove razloge
- **Scalability** strategije

**Ključni principi:**
1. 🎯 **Separation of Concerns** - Draft vs Corpus
2. 🔄 **Flexibility** - JSON za fleksibilne strukture
3. ⚡ **Performance** - Caching i indeksi
4. 📈 **Scalability** - Paralelizacija i distribucija
5. 🛠️ **Maintainability** - Jasne odgovornosti entiteta