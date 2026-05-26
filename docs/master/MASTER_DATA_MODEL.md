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

### ImportJob

```json
{
  "import_job_id": "uuid",
  "corpus_id": "uuid",
  "folder_uri": "file:///D:/laws",
  "status": "completed",
  "total_files": 3,
  "supported_files": 2,
  "unsupported_files": 1,
  "started_at": "datetime",
  "completed_at": "datetime",
  "error_message": null
}
```

### ImportReport

```json
{
  "import_job_id": "uuid",
  "corpus_id": "uuid",
  "status": "completed",
  "source_files": [],
  "warnings": [],
  "summary": {
    "total_files": 3,
    "supported_files": 2,
    "unsupported_files": 1,
    "duplicate_files": 0
  }
}
```

### ExtractedDocument

```json
{
  "source_uri": "file:///D:/laws/Zakon.txt",
  "filename": "Zakon.txt",
  "file_type": "txt",
  "content_text": "Full extracted text",
  "language_code": "sr",
  "extraction_status": "completed",
  "error_message": null,
  "metadata": {
    "character_count": 1234,
    "page_count": 1,
    "paragraph_count": null,
    "normalization_applied": true,
    "normalization": "sr_cyrillic_to_latin"
  }
}
```

### ParsedLegalDocument

```json
{
  "source_uri": "file:///D:/laws/Zakon.txt",
  "filename": "Zakon.txt",
  "document_type": "law",
  "title": "Zakon o ...",
  "language_code": "sr",
  "legal_units": [
    {
      "legal_unit_id": "uuid",
      "parent_legal_unit_id": null,
      "unit_type": "article",
      "number": "1",
      "ordinal": 1,
      "heading": null,
      "content_text": "Article text",
      "path": "article:1"
    }
  ],
  "metadata": {
    "section_count": 0,
    "article_count": 1,
    "paragraph_count": 2,
    "item_count": 0
  }
}
```

### CanonicalDocument

```json
{
  "source_uri": "file:///D:/laws/Zakon.txt",
  "filename": "Zakon.txt",
  "document_type": "law",
  "title": "Zakon o ...",
  "language_code": "sr",
  "canonical_json": {
    "schema_version": "0.1",
    "document": {},
    "legal_units": [],
    "metadata": {}
  }
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

Stored document summaries include `corpus_id` when created by corpus import, so
retrieval can filter results by corpus.

Allowed `document_type` for Serbian MVP:

- `law` for `zakon`
- `regulation` for `uredba`
- `rulebook` for `pravilnik`
- `order` for `naredba`
- `strategy` for `strategija`
- `unknown` when the type cannot be identified with sufficient confidence

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

Serbian legal structure to Akoma Ntoso mapping:

- `deo` -> `part`
- `glava` -> `chapter`
- `odeljak` -> `section`
- `pododeljak` -> `subsection`
- `clan` / `član` -> `article`
- `stav` -> `paragraph`
- `tacka` / `tačka` -> `point`
- `podtacka` / `podtačka` -> `hcontainer name="subpoint"` in Akoma export and
  `subitem` in the internal canonical model
- `alineja` -> `alinea`

Allowed hierarchy for Serbian Akoma export:

- `part` contains `chapter`
- `chapter` contains `section`, `article`, or `intro`
- `section` contains `subsection` or `article`
- `subsection` contains `article`
- `article` contains `paragraph` or `intro`
- `paragraph` contains `point`, `alinea`, or `intro`
- `point` contains `subitem` or `intro`
- `subitem` contains `alinea` or `intro`

Parser MVP extracts inline Serbian item markers such as `1) ... 2) ...` as
internal `item` legal units below the containing paragraph.
It also extracts inline subitem markers such as `(1) ... (2) ...` below an item
and alinea markers such as `- ...` below a paragraph.

Akoma FRBR export naming:

- country: `rs`
- document type: `act` for MVP legislation exports
- language: `srp` for Serbian, regardless of original Cyrillic or Latin script
- manifestation format: `xml`

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

### ExtractedDefinition

```json
{
  "definition_id": "uuid",
  "source_legal_unit_id": "uuid",
  "source_path": "article:2/paragraph:1",
  "term": "Ministarstvo",
  "definition_text": "ministarstvo nadlezno za poslove sumarstva",
  "confidence": 0.78
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

Allowed `reference_type` for MVP:

- `article_reference`
- `official_gazette_reference`

Internal article references can resolve to article, paragraph, or item paths
when the reference includes `clan`, optional `stav`, and optional `tacka`.

### DraftReview

```json
{
  "pipeline_run_id": "uuid",
  "title": "Nacrt zakona o ...",
  "language_code": "sr",
  "selected_corpus_id": "uuid",
  "status": "completed",
  "finding_count": 1,
  "created_at": "datetime",
  "updated_at": "datetime",
  "metadata": {
    "document_type": "law",
    "classification_confidence": 0.95,
    "reference_count": 1,
    "resolved_reference_count": 1
  }
}
```

MVP draft reviews accept draft text, normalize Serbian Cyrillic to Latin when
enabled, parse the legal structure, canonicalize it, extract and resolve
references, then store review findings and run artifacts.
When `selected_corpus_id` is present, the review run also stores corpus-scoped
retrieval results as a review artifact for later evidence/reporting use.

Draft reviews can also be created from supported local files (`txt`, `pdf`,
`docx`) through the same extraction service used by corpus imports. The record
metadata stores `input_type`, `source_uri`, `filename`, `file_type`, and
extraction metadata when the draft originates from a file.

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
  "created_at": "datetime",
  "updated_at": "datetime",
  "review_note": "Expert review note"
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

### Report

```json
{
  "report_id": "uuid",
  "pipeline_run_id": "uuid",
  "report_format": "markdown | docx | pdf",
  "title": "Izvestaj - Nacrt zakona",
  "finding_count": 1,
  "content_text": "# Izvestaj ...",
  "metadata": {
    "draft_review_status": "completed",
    "document_type": "law"
  },
  "created_at": "datetime"
}
```

MVP reports are stored artifacts generated from draft review findings. Markdown
is stored as text; DOCX and PDF store generated download artifact paths in
metadata.

