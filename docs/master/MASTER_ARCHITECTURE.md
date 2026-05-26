# MASTER_ARCHITECTURE

This document is the golden copy for zAIkon architecture.

## Product Definition

zAIkon is an AI-assisted legislative compliance review platform. It processes
existing laws and regulations into a structured corpus, then reviews uploaded
draft laws against that corpus.

The system produces findings, not final legal determinations. A finding is a
cited, reviewable signal that a lawyer must accept, reject, or mark as partial.

## Architectural Style

Initial deployment: modular monolith.

Future-ready boundary: each module must be extractable into a Dockerized
microservice. Modules communicate through explicit request/response contracts,
even when the implementation is an in-process Python call.

## Core Modules

1. `corpus`
   - Owns corpus records and folder import jobs.
   - Scans folders and tracks source files.

2. `documents`
   - Extracts text from PDF, DOCX, TXT, and future formats.
   - Produces `ExtractedDocument`.

3. `legal_parser`
   - Parses legal structure: document, article, paragraph, item, subitem.
   - Produces `ParsedLegalDocument`.

4. `canonical`
   - Converts parsed documents to canonical JSON.
   - Later supports Akoma Ntoso XML import/export.

5. `references`
   - Extracts and resolves legal references.
   - Produces `LegalReference` and `ResolvedReference`.

6. `indexing`
   - Builds keyword, vector, metadata, structure, and reference indexes.

7. `retrieval`
   - Performs hybrid retrieval:
     - keyword/BM25
     - vector search
     - tree/structure search
     - reference search
     - graph traversal
     - reranking

8. `checkers`
   - Runs domain-specific compliance checks.
   - Produces `Finding`.

9. `llm`
   - Parses user intent.
   - Expands legal queries.
   - Generates Serbian-language explanations and drafting suggestions.
   - Enforces citation-grounded answers through a citation guard.

10. `reports`
    - Generates review reports in HTML, DOCX, and PDF in later phases.

## Data Flow

Corpus ingestion:

```text
Folder
→ ScanFolderStep
→ ExtractTextStep
→ ParseLegalStructureStep
→ ConvertToCanonicalJsonStep
→ ExtractReferencesStep
→ ResolveReferencesStep
→ BuildIndexesStep
→ BuildGraphLinksStep
→ GenerateImportReportStep
```

Draft review:

```text
Draft upload
→ ExtractTextStep
→ ParseLegalStructureStep
→ ConvertToCanonicalJsonStep
→ ExtractReferencesStep
→ HybridRetrieveRelevantLawStep
→ RunComplianceCheckersStep
→ GenerateFindingsStep
→ GenerateReviewReportStep
```

Interactive AI:

```text
User request
→ IntentParser
→ QueryPlanner
→ QueryExpansion
→ HybridRetriever
→ Checker or DraftingAssistant
→ CitationGuard
→ AnswerGenerator
```

## Storage Strategy

Canonical working model:

- PostgreSQL `jsonb` in production.
- SQLite JSON text during early scaffold/MVP if needed.

Search/index storage:

- Full-text: PostgreSQL FTS or OpenSearch later.
- Vector: Qdrant.
- Graph: PostgreSQL edge tables for MVP, Neo4j/GraphDB later.
- Artifacts: local filesystem for MVP, S3/MinIO later.

## Language Strategy

Phase 1:

- Serbian.
- Cyrillic/Latin normalization.
- Internal storage and indexes use normalized Latin `content_text`.
- Akoma Ntoso export uses ISO 639-2 language value `srp` for Serbian, regardless
  of source script.

Phase 2:

- Macedonian.
- Shared canonical data model and language-specific parser/reference rules.

## Non-Negotiables

- No uncited compliance conclusion.
- No LLM-only legal judgment.
- Every finding must include evidence.
- Every module must have regression fixtures.
- Master documents are updated before schema or API changes.

## Serbian Akoma Ntoso Direction

The Serbian Akoma implementation follows the layered approach described in
`Automatic Transformation of Plain-text Legislation into Machine-readable
Format` by Cvejic et al.:

1. metadata layer
2. structural/hierarchical layer
3. text/reference layer

Akoma Ntoso / LegalDocML remains an import/export and interoperability format.
The runtime canonical model remains JSON. Parser and canonical modules should
preserve enough structure to export valid Akoma later without reparsing raw text.

Initial Akoma support should prioritize deterministic hierarchy parsing and
schema validation. Metadata and references are expected to require human review
or confidence scoring because published Serbian regulations vary in formatting
and reference style.

