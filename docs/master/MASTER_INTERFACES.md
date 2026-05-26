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

## Document Service

```python
extract_text(request: ExtractTextRequest) -> ExtractTextResponse
classify_document(request: ClassifyDocumentRequest) -> ClassifyDocumentResponse
```

## Legal Parser Service

```python
parse_legal_structure(request: ParseLegalStructureRequest) -> ParseLegalStructureResponse
```

## Canonical Service

```python
to_canonical_json(request: CanonicalizeRequest) -> CanonicalizeResponse
export_akoma_ntoso(request: ExportAkomaNtosoRequest) -> ExportAkomaNtosoResponse
```

## Reference Service

```python
extract_references(request: ExtractReferencesRequest) -> ExtractReferencesResponse
resolve_references(request: ResolveReferencesRequest) -> ResolveReferencesResponse
```

## Indexing Service

```python
build_indexes(request: BuildIndexesRequest) -> BuildIndexesResponse
refresh_indexes(request: RefreshIndexesRequest) -> RefreshIndexesResponse
```

## Retrieval Service

```python
hybrid_search(request: HybridSearchRequest) -> HybridSearchResponse
retrieve_for_legal_unit(request: RetrieveForLegalUnitRequest) -> RetrieveForLegalUnitResponse
```

## Checker Service

```python
run_checker(request: RunCheckerRequest) -> RunCheckerResponse
run_checker_suite(request: RunCheckerSuiteRequest) -> RunCheckerSuiteResponse
```

## LLM Service

```python
parse_intent(request: ParseIntentRequest) -> ParseIntentResponse
expand_query(request: ExpandQueryRequest) -> ExpandQueryResponse
generate_answer(request: GenerateAnswerRequest) -> GenerateAnswerResponse
suggest_revision(request: SuggestRevisionRequest) -> SuggestRevisionResponse
```

## Report Service

```python
generate_report(request: GenerateReportRequest) -> GenerateReportResponse
```

