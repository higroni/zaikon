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
4. `identify_legal_documents`
5. `parse_legal_structure`
6. `convert_to_canonical_json`
7. `extract_references`
8. `extract_definitions`
9. `store_documents`
10. `build_keyword_index`
11. `build_vector_index`
12. `build_structure_index`
13. `build_reference_graph`
14. `generate_import_report`

## DraftComplianceReviewChain

1. `upload_draft`
2. `extract_text`
3. `parse_legal_structure`
4. `convert_to_canonical_json`
5. `extract_references`
6. `resolve_references`
7. `retrieve_relevant_law`
8. `run_reference_checker`
9. `run_definition_checker`
10. `run_terminology_checker`
11. `run_temporal_validity_checker`
12. `generate_findings`
13. `generate_review_report`

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
- `extracted_documents`
- `parsed_legal_documents`
- `canonical_documents`
- `extracted_references`
- `resolved_references`
- `keyword_index_report`
- `vector_index_report`
- `structure_index_report`
- `reference_graph_report`
- `retrieval_results`
- `checker_findings`
- `review_report`

