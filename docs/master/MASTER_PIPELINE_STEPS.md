# MASTER_PIPELINE_STEPS

This document is the golden copy for pipeline step names and contracts.

## Pipeline Contract

Each step:

- has a unique `step_name`
- reads from `PipelineContext`
- writes named artifacts to `PipelineContext`
- emits structured logs
- is idempotent where possible
- can be regression tested from fixtures

## Step Status

- `pending`
- `running`
- `completed`
- `failed`
- `skipped`
- `cancelled`

## CorpusFolderImportChain

1. `scan_folder`
2. `detect_file_types`
3. `extract_text`
4. `normalize_text`
5. `identify_legal_documents`
6. `parse_legal_structure`
7. `convert_to_canonical_json`
8. `extract_references`
9. `resolve_references`
10. `extract_definitions`
11. `store_documents`
12. `build_keyword_index`
13. `build_vector_index`
14. `build_structure_index`
15. `build_reference_graph`
16. `generate_import_report`

## DraftComplianceReviewChain

1. `upload_draft`
2. `extract_text`
3. `normalize_text`
4. `parse_legal_structure`
5. `convert_to_canonical_json`
6. `extract_references`
7. `resolve_references`
8. `retrieve_relevant_law`
9. `run_reference_checker`
10. `run_definition_checker`
11. `run_terminology_checker`
12. `run_temporal_validity_checker`
13. `generate_findings`
14. `generate_review_report`

## InteractiveLegalAssistantChain

1. `parse_user_intent`
2. `plan_query`
3. `expand_query`
4. `hybrid_retrieve`
5. `rerank_results`
6. `run_targeted_checker`
7. `generate_answer`
8. `citation_guard`

## Artifact Names

Use these exact names:

- `source_file_manifest`
- `import_report`
- `extracted_documents`
- `normalized_documents`
- `identified_documents`
- `parsed_legal_documents`
- `canonical_documents`
- `extracted_references`
- `resolved_references`
- `extracted_definitions`
- `stored_documents_report`
- `keyword_index_report`
- `vector_index_report`
- `structure_index_report`
- `reference_graph_report`
- `retrieval_results`
- `checker_findings`
- `review_report`

