# MASTER_API_ENDPOINTS

This document is the golden copy for HTTP API endpoints.

Base path: `/api/v1`

## Health

- `GET /health`
- `GET /api/v1/modules/health`

## Corpus

- `POST /api/v1/corpora`
- `GET /api/v1/corpora`
- `GET /api/v1/corpora/{corpus_id}`
- `POST /api/v1/corpora/{corpus_id}/import-folder`
- `GET /api/v1/corpora/{corpus_id}/import-jobs`
- `GET /api/v1/import-jobs/{import_job_id}`
- `GET /api/v1/import-jobs/{import_job_id}/report`
- `GET /api/v1/import-jobs/{import_job_id}/artifacts`
- `GET /api/v1/import-jobs/{import_job_id}/artifacts/{artifact_name}`

## Documents

- `GET /api/v1/documents`
- `GET /api/v1/documents/{document_id}`
- `GET /api/v1/documents/{document_id}/akoma-ntoso`
- `GET /api/v1/document-versions/{document_version_id}`
- `GET /api/v1/legal-units/{legal_unit_id}`

## Draft Reviews

- `POST /api/v1/draft-reviews`
- `POST /api/v1/draft-reviews/from-file`
- `GET /api/v1/draft-reviews`
- `GET /api/v1/draft-reviews/{pipeline_run_id}`
- `POST /api/v1/draft-reviews/{pipeline_run_id}/run`
- `GET /api/v1/draft-reviews/{pipeline_run_id}/findings`

## Findings

- `GET /api/v1/findings`
- `GET /api/v1/findings/{finding_id}`
- `PATCH /api/v1/findings/{finding_id}/review-decision`

## Search

- `POST /api/v1/search/hybrid`
- `POST /api/v1/search/legal-unit`

## Assistant

- `POST /api/v1/assistant/sessions`
- `POST /api/v1/assistant/sessions/{session_id}/messages`
- `GET /api/v1/assistant/sessions/{session_id}/messages`

## Reports

- `POST /api/v1/reports`
- `GET /api/v1/reports`
- `GET /api/v1/reports/{report_id}`
- `GET /api/v1/reports/{report_id}/download`

