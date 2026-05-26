# MASTER_PROMPT

Use this prompt when starting a new Codex/ChatGPT session for zAIkon.

---

You are working on `zAIkon`, located at:

```text
D:\POSAO\OllamaProjects\ZAIKON
```

zAIkon is a new AI-assisted legislative compliance review platform. It is
separate from, but inspired by, the existing `PDF2GPU` project at:

```text
D:\POSAO\OllamaProjects\PDF2GPU
```

The product goal is to process a corpus of existing laws and regulations in
Serbian first, later Macedonian, then review uploaded draft laws or draft
regulations against that processed corpus. The system should identify potential
non-compliance, explain why, cite relevant provisions, and suggest harmonized
wording where possible.

Important: zAIkon is a decision-support system for lawyers, not an autonomous
legal decision-maker. It should produce cited findings and recommendations that
a human reviewer can accept, reject, or mark as partial.

## Core Architectural Direction

Build zAIkon as a modular monolith first, with strict module contracts so each
module can later become a separate Docker service or microservice.

Every domain module must be self-sustained:

- has a clear domain boundary
- exposes API/service contracts
- has request/response schemas
- has configuration keys
- has unit tests
- has contract tests
- has regression fixtures where applicable
- can later be extracted behind HTTP without changing upstream code

## Golden Copy Rule

Before adding or changing schemas, field names, endpoint names, status values,
or pipeline step names, read and update the relevant master document in:

```text
D:\POSAO\OllamaProjects\ZAIKON\docs\master
```

The master documents are the source of truth:

- `MASTER_ARCHITECTURE.md`
- `MASTER_DATA_MODEL.md`
- `MASTER_INTERFACES.md`
- `MASTER_PIPELINE_STEPS.md`
- `MASTER_CONFIG.md`
- `MASTER_API_ENDPOINTS.md`
- `MASTER_TESTING_STRATEGY.md`
- `MASTER_UI_JOURNEYS.md`
- `MASTER_GLOSSARY.md`
- `MASTER_PROMPT.md`

Do not introduce synonyms for the same concept. Use the names from
`MASTER_GLOSSARY.md`. For example:

- use `document_id`, not `doc_id`
- use `article_id`, not `clan_id`
- use `paragraph_id`, not `stav_id`
- use `source_uri`, not mixed `file_path`/`source_path`
- use `canonical_json`, not `legal_json`
- use `finding`, not `issue`

## JSON vs XML Decision

The runtime canonical legal model is JSON.

Akoma Ntoso / LegalDocML XML is supported later as import/export and
interoperability format, not the primary working representation.

Recommended flow:

```text
PDF/DOCX/TXT/HTML/XML
→ extracted text
→ parsed legal structure
→ internal canonical JSON
→ indexes + graph + embeddings
→ optional Akoma Ntoso XML export
```

## Corpus Import Requirement

The system must support importing an entire folder containing laws and
regulations in:

- PDF
- TXT
- DOCX / Word

Future formats may include HTML, XML, RTF, and OCR-scanned PDFs.

The corpus folder import chain should:

```text
Scan folder
→ detect file type
→ extract text
→ identify legal document
→ parse legal structure
→ convert to canonical JSON
→ extract references
→ extract definitions
→ store document
→ build keyword index
→ build vector index
→ build structure index
→ build reference graph
→ generate import report
```

## Draft Compliance Review Requirement

The system must support uploading a draft law or regulation in DOCX/PDF/TXT,
then running a compliance review against a selected corpus.

Draft review flow:

```text
Draft upload
→ extract text
→ parse legal structure
→ convert to canonical JSON
→ extract references
→ resolve references
→ retrieve relevant existing law
→ run compliance checkers
→ generate findings
→ generate review report
```

## LLM Role

The LLM is required, especially for Serbian-language interaction and answer
formation. It should participate in:

- understanding user requests
- parsing intent
- query planning
- query expansion
- hybrid retrieval support
- explanation generation
- drafting suggestions
- Serbian-language answer formatting

The LLM must not be the only source of truth. Deterministic structure, indexes,
references, citations, and checker outputs must ground answers.

Preferred pattern:

```text
LLM parses and plans
→ system retrieves through keyword/vector/tree/reference/graph search
→ deterministic and LLM-assisted checkers produce findings
→ LLM explains findings and proposes wording
→ citation guard verifies grounding
→ human reviewer decides
```

Avoid:

```text
LLM reads everything and gives an unsupported legal conclusion
```

## Hybrid Retrieval Requirement

Relevant provisions should be found through a hybrid model:

- keyword/BM25 search
- semantic vector search
- tree/structure search
- reference resolver
- graph traversal
- LLM query expansion/planning
- reranking

PDF2GPU can be used as a reference for Qdrant, embeddings, reranking, and RAG
patterns, but zAIkon must have legal-aware parsing and indexing.

## MVP Scope

First MVP should focus on Serbian and include:

1. Corpus folder import for PDF/DOCX/TXT
2. Legal structure parsing into articles/paragraphs/items
3. Canonical JSON model
4. Reference extraction
5. Basic reference resolution
6. Keyword and vector indexing
7. Hybrid retrieval
8. Draft document upload
9. Reference checker
10. Terminology/definition checker skeleton
11. Findings model and findings table
12. Serbian LLM answer/drafting assistant skeleton
13. Regression fixtures and automated tests

Macedonian support is Phase 2, but design must remain multilingual from the
start via `language_code`.

## Current Scaffold

The project already contains:

```text
README.md
requirements.txt
pyproject.toml
.gitignore
docs/master/*.md
backend/zaikon/main.py
backend/zaikon/core/config.py
backend/zaikon/core/schemas.py
backend/zaikon/pipeline/base.py
backend/zaikon/pipeline/context.py
backend/zaikon/pipeline/chains.py
backend/zaikon/pipeline/steps/dummy.py
backend/zaikon/api/routers/health.py
backend/zaikon/api/routers/pipeline.py
backend/tests/*
```

The current backend has:

- `GET /health`
- `GET /api/v1/modules/health`
- `POST /api/v1/pipeline/echo`

Initial tests pass with:

```powershell
cd D:\POSAO\OllamaProjects\ZAIKON
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

## Development Instructions

When continuing development:

1. Read relevant `docs/master` documents before coding.
2. Update master docs before changing contracts.
3. Keep modules domain-bounded.
4. Add tests with every module.
5. Prefer small vertical slices:
   - schema
   - service
   - route
   - fixture
   - tests
6. Keep zAIkon independent from PDF2GPU, but reuse ideas/code patterns where
   appropriate.

## Suggested Next Step

Implement Phase 1 / first real module:

`CorpusFolderImportChain` skeleton with:

- `ScanFolderStep`
- `DetectFileTypesStep`
- request/response schemas
- service interface
- API endpoint:
  - `POST /api/v1/corpora`
  - `POST /api/v1/corpora/{corpus_id}/import-folder`
- regression fixture with a small folder containing `.txt`
- contract and unit tests

Keep parsing/extraction minimal at first. The first goal is to prove the module
boundary, pipeline execution, import report shape, and regression testing
pattern.

---

Start by inspecting the repository and the master documents, then continue from
the suggested next step unless the user gives a different priority.

