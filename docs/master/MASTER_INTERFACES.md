# MASTER_INTERFACES

This document is the golden copy for module interfaces.

## Interface Rule

Each module exposes a service class with request and response schemas. In-process
calls must use the same schema shape that future HTTP APIs will expose.

## Base Module Contract

Every module must provide:

- `health() -> ModuleHealth`
- domain service methods
- request/response schemas
- module-level config
- unit tests
- contract tests
- regression fixtures

## Common Response Envelope

```json
{
  "success": true,
  "data": {},
  "errors": [],
  "warnings": [],
  "metadata": {}
}
```

## Corpus Service

```python
create_corpus(request: CreateCorpusRequest) -> CreateCorpusResponse
import_folder(request: ImportFolderRequest) -> ImportFolderResponse
get_import_report(import_job_id: str) -> ImportReportResponse
```

Initial schema names:

- `CreateCorpusRequest`
- `CreateCorpusResponse`
- `ImportFolderRequest`
- `ImportFolderResponse`
- `ImportReportResponse`
- `CorpusRecord`
- `SourceFileRecord`
- `ImportJobRecord`
- `ImportReport`

## Document Service

```python
extract_text(request: ExtractTextRequest) -> ExtractTextResponse
classify_document(request: ClassifyDocumentRequest) -> ClassifyDocumentResponse
```

Document catalog endpoints support optional `corpus_id` filtering when listing
stored documents. Imported document summaries expose `document_version_id`, and
`GET /api/v1/document-versions/{document_version_id}` returns the canonical JSON
for that stored version.

Initial schema names:

- `ExtractTextRequest`
- `ExtractTextResponse`
- `ExtractedDocument`
- `ClassifyDocumentRequest`
- `ClassifyDocumentResponse`
- `document_type` values: `law`, `regulation`, `rulebook`, `order`, `strategy`,
  `unknown`

## Legal Parser Service

```python
parse_legal_structure(request: ParseLegalStructureRequest) -> ParseLegalStructureResponse
```

Initial schema names:

- `ParseLegalStructureRequest`
- `ParseLegalStructureResponse`
- `ParsedLegalDocument`
- `ParsedLegalUnit`

## Canonical Service

```python
to_canonical_json(request: CanonicalizeRequest) -> CanonicalizeResponse
export_akoma_ntoso(request: ExportAkomaNtosoRequest) -> ExportAkomaNtosoResponse
```

Initial schema names:

- `CanonicalizeRequest`
- `CanonicalizeResponse`
- `CanonicalDocument`
- `ExportAkomaNtosoRequest`
- `ExportAkomaNtosoResponse`

## Reference Service

```python
extract_references(request: ExtractReferencesRequest) -> ExtractReferencesResponse
resolve_references(request: ResolveReferencesRequest) -> ResolveReferencesResponse
```

Initial schema names:

- `ExtractReferencesRequest`
- `ExtractReferencesResponse`
- `ResolveReferencesRequest`
- `ResolveReferencesResponse`
- `LegalReferenceRecord`
- `ResolvedReferenceRecord`

## Indexing Service

```python
build_indexes(request: BuildIndexesRequest) -> BuildIndexesResponse
refresh_indexes(request: RefreshIndexesRequest) -> RefreshIndexesResponse
```

Initial schema names:

- `BuildIndexesRequest`
- `BuildIndexesResponse`
- `RefreshIndexesRequest`
- `RefreshIndexesResponse`
- `IndexReport`

## Retrieval Service

```python
hybrid_search(request: HybridSearchRequest) -> HybridSearchResponse
retrieve_for_legal_unit(request: RetrieveForLegalUnitRequest) -> RetrieveForLegalUnitResponse
```

Initial schema names:

- `HybridSearchRequest`
- `HybridSearchResponse`
- `RetrieveForLegalUnitRequest`
- `RetrieveForLegalUnitResponse`
- `RetrievalResult`

Search requests accept optional `corpus_id` to limit retrieval to one corpus.

## Checker Service

```python
ReferenceChecker.check(
    pipeline_run_id: UUID,
    references: list[LegalReferenceRecord],
    resolved_references: list[ResolvedReferenceRecord],
) -> list[FindingRecord]
DefinitionConsistencyChecker.check(
    pipeline_run_id: UUID,
    document: CanonicalDocument,
) -> list[FindingRecord]
```

Initial schema names:

- `FindingRecord`
- `UpdateFindingReviewDecisionRequest`
- `UpdateFindingReviewDecisionResponse`

Finding list endpoints support optional `pipeline_run_id` and `status` filters.

## Draft Review Service

```python
create_draft_review(request: CreateDraftReviewRequest) -> CreateDraftReviewResponse
create_draft_review_from_file(request: CreateDraftReviewFromFileRequest) -> CreateDraftReviewResponse
list_draft_reviews() -> list[DraftReviewRecord]
get_draft_review(pipeline_run_id: UUID) -> DraftReviewDetail | None
run_draft_review(pipeline_run_id: UUID) -> RunDraftReviewResponse
list_findings(pipeline_run_id: UUID) -> list[FindingRecord]
export_akoma_ntoso(pipeline_run_id: UUID) -> str | None
list_artifacts(pipeline_run_id: UUID) -> list[str] | None
get_artifact(pipeline_run_id: UUID, artifact_name: str) -> Any
```

Initial schema names:

- `CreateDraftReviewRequest`
- `CreateDraftReviewFromFileRequest`
- `CreateDraftReviewResponse`
- `DraftReviewRecord`
- `DraftReviewDetail`
- `RunDraftReviewResponse`
- `FindingRecord`

## LLM Service

```python
parse_intent(request: ParseIntentRequest) -> ParseIntentResponse
expand_query(request: ExpandQueryRequest) -> ExpandQueryResponse
generate_answer(request: GenerateAnswerRequest) -> GenerateAnswerResponse
suggest_revision(request: SuggestRevisionRequest) -> SuggestRevisionResponse
```

Initial schema names:

- `ParseIntentRequest`
- `ParseIntentResponse`
- `ExpandQueryRequest`
- `ExpandQueryResponse`
- `GenerateAnswerRequest`
- `GenerateAnswerResponse`
- `SuggestRevisionRequest`
- `SuggestRevisionResponse`

## Assistant Service

```python
create_session(request: CreateAssistantSessionRequest) -> CreateAssistantSessionResponse
create_message(session_id: UUID, request: CreateAssistantMessageRequest) -> CreateAssistantMessageResponse
list_messages(session_id: UUID) -> list[AssistantMessageRecord] | None
```

Initial schema names:

- `CreateAssistantSessionRequest`
- `CreateAssistantSessionResponse`
- `AssistantSessionRecord`
- `CreateAssistantMessageRequest`
- `CreateAssistantMessageResponse`
- `AssistantMessageRecord`

## Report Service

```python
generate_report(request: GenerateReportRequest) -> GenerateReportResponse
list_reports() -> list[ReportRecord]
get_report(report_id: UUID) -> ReportRecord | None
```

Initial schema names:

- `GenerateReportRequest`
- `GenerateReportResponse`
- `ReportRecord`

Supported `report_format` values:

- `markdown`
- `docx`
- `pdf`

