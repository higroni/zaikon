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

Phase 0 scaffold:

- Master planning documents
- FastAPI backend skeleton
- Pipeline base contracts
- Example health and pipeline endpoints
- Initial tests

