# MASTER_DATA_MODEL

This document is the golden copy for zAIkon entities and schema names.

## Storage Principle

The canonical application model is JSON. Akoma Ntoso XML is an interoperability
format, not the primary runtime representation.

## Core Entities

### Corpus

```json
{
  "corpus_id": "uuid",
  "name": "Poreski propisi RS",
  "description": "Corpus description",
  "language_code": "sr",
  "domain": "tax",
  "status": "active",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### SourceFile

```json
{
  "source_file_id": "uuid",
  "corpus_id": "uuid",
  "source_uri": "file:///D:/laws/Zakon.pdf",
  "filename": "Zakon.pdf",
  "file_type": "pdf",
  "content_hash": "sha256",
  "size_bytes": 12345,
  "import_status": "completed",
  "error_message": null,
  "created_at": "datetime"
}
```

### Document

```json
{
  "document_id": "uuid",
  "corpus_id": "uuid",
  "source_file_id": "uuid",
  "document_type": "law",
  "title": "Zakon o ...",
  "short_title": "Zakon o ...",
  "language_code": "sr",
  "jurisdiction": "RS",
  "canonical_json": {},
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### DocumentVersion

```json
{
  "document_version_id": "uuid",
  "document_id": "uuid",
  "version_label": "official_gazette_2024_10",
  "published_at": "date",
  "effective_from": "date",
  "valid_from": "date",
  "valid_to": null,
  "source_uri": "https://...",
  "canonical_json": {}
}
```

### LegalUnit

```json
{
  "legal_unit_id": "uuid",
  "document_version_id": "uuid",
  "parent_legal_unit_id": null,
  "unit_type": "article",
  "number": "1",
  "ordinal": 1,
  "heading": null,
  "content_text": "Text of the unit",
  "path": "article:1",
  "canonical_json": {}
}
```

Allowed `unit_type`:

- `document`
- `part`
- `chapter`
- `section`
- `article`
- `paragraph`
- `item`
- `subitem`
- `transitional_provision`
- `final_provision`

### LegalReference

```json
{
  "reference_id": "uuid",
  "source_legal_unit_id": "uuid",
  "raw_text": "član 5. stav 2.",
  "reference_type": "article_reference",
  "target_document_title": "Zakon o radu",
  "target_article_number": "5",
  "target_paragraph_number": "2",
  "confidence": 0.93
}
```

### ResolvedReference

```json
{
  "resolved_reference_id": "uuid",
  "reference_id": "uuid",
  "target_legal_unit_id": "uuid",
  "resolution_status": "resolved",
  "resolution_note": null
}
```

Allowed `resolution_status`:

- `resolved`
- `ambiguous`
- `missing`
- `stale`
- `out_of_scope`

### Finding

```json
{
  "finding_id": "uuid",
  "pipeline_run_id": "uuid",
  "finding_type": "reference_missing",
  "risk_level": "high",
  "status": "open",
  "title": "Missing referenced article",
  "explanation": "The draft refers to article 12, but no such article exists.",
  "recommendation": "Update the reference or add the missing provision.",
  "source_legal_unit_id": "uuid",
  "created_at": "datetime"
}
```

Allowed `finding_type` for MVP:

- `reference_missing`
- `reference_stale`
- `definition_conflict`
- `terminology_inconsistent`
- `temporal_validity_issue`
- `possible_norm_conflict`
- `possible_overlap`
- `drafting_style_warning`

### Evidence

```json
{
  "evidence_id": "uuid",
  "finding_id": "uuid",
  "evidence_type": "citation",
  "document_id": "uuid",
  "legal_unit_id": "uuid",
  "quote": "Relevant quote",
  "source_uri": "file:///...",
  "relevance_score": 0.87
}
```

