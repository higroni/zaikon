# MASTER_GLOSSARY

This is the golden copy for naming. Do not introduce synonyms in code,
database fields, APIs, or UI without updating this file first.

## Canonical Entity Names

- `corpus`: a named collection of processed laws and regulations.
- `source_file`: a physical file discovered during import.
- `document`: a legal document or draft legal document.
- `document_type`: category of legal document, such as `law`, `regulation`,
  `rulebook`, `order`, or `strategy`.
- `document_version`: a version of a legal document valid in a time interval.
- `legal_unit`: any addressable part of a document.
- `article`: a legal unit at article level.
- `paragraph`: a legal unit within an article.
- `item`: a legal unit within a paragraph; Serbian inline markers such as `1)`
  are parsed below the containing paragraph.
- `alinea`: a legal unit within a paragraph, commonly introduced by a dash in
  extracted Serbian legal text.
- `reference`: a detected citation or legal reference.
- `resolved_reference`: a reference linked to a target legal unit.
- `index_job`: a job that creates or refreshes indexes.
- `pipeline_run`: one execution of a chain.
- `pipeline_artifact`: any output created by a pipeline step.
- `finding`: a potential compliance issue.
- `evidence`: source text supporting a finding.
- `review_decision`: human decision on a finding.
- `akoma_ntoso`: LegalDocML/Akoma Ntoso XML interoperability format.
- `frbr_uri`: Akoma Ntoso FRBR URI identifying a work, expression, or
  manifestation.
- `subitem`: internal canonical representation of Serbian `podtačka`; exported
  to Akoma as `hcontainer name="subpoint"`.

## Required Field Names

Use these exact names:

- `corpus_id`
- `source_file_id`
- `document_id`
- `document_version_id`
- `legal_unit_id`
- `article_id`
- `paragraph_id`
- `reference_id`
- `resolved_reference_id`
- `pipeline_run_id`
- `pipeline_step_id`
- `artifact_id`
- `finding_id`
- `evidence_id`
- `source_uri`
- `canonical_json`
- `content_text`
- `language_code`
- `created_at`
- `updated_at`

## Avoided Synonyms

Do not use:

- `doc_id` instead of `document_id`
- `clan_id` instead of `article_id`
- `stav_id` instead of `paragraph_id`
- `file_path` for sources; use `source_uri`
- `legal_json` or `body_json`; use `canonical_json`
- `issue` for compliance output; use `finding`

## Status Values

Pipeline/job status:

- `pending`
- `running`
- `completed`
- `failed`
- `cancelled`

Finding status:

- `open`
- `accepted`
- `rejected`
- `partial`
- `needs_expert_review`

Risk levels:

- `critical`
- `high`
- `medium`
- `low`
- `info`

Language codes:

- `sr`
- `mk`

