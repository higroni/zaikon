# zAIkon

AI-assisted legislative compliance review platform.

zAIkon is a modular system for importing legal corpora, parsing legislation into
a canonical model, indexing legal provisions, checking draft laws against the
processed corpus, and producing cited findings and Serbian-language explanations.

The project starts as a modular monolith with strict contracts. Each domain
module is designed so it can later be extracted into a separate Docker service
without changing its public interface.

## First Principles

- The canonical working format is JSON, with optional Akoma Ntoso XML
  import/export for interoperability.
- LLMs assist with intent parsing, query expansion, explanation, and drafting,
  but do not replace deterministic checks, structured references, citations, or
  human legal review.
- Every module owns a domain boundary, API contract, configuration surface,
  fixtures, and regression tests.
- Master documents in `docs/master` are the golden copy for names, schemas,
  API contracts, pipeline steps, and status values.

## Current Status

Backend MVP in progress:

- FastAPI modular-monolith backend
- corpus folder import for TXT, PDF, and DOCX
- Serbian Cyrillic-to-Latin normalization before parsing/indexing
- document classification for laws, regulations, rulebooks, orders, strategies,
  and unknown documents
- legal structure parsing into articles, paragraphs, items, subitems, and alineas
- canonical JSON model and Akoma Ntoso XML export
- reference extraction/resolution and deterministic draft checkers
- lexical retrieval over imported legal units with corpus filtering
- draft review creation from text or file, with findings and artifacts
- Markdown, DOCX, and PDF report generation
- grounded assistant API skeleton with deterministic intent/query/answer flow

Run tests with:

```powershell
python -m pytest backend\tests -q
```

