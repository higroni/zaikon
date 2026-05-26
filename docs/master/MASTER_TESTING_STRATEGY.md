# MASTER_TESTING_STRATEGY

This document is the golden copy for zAIkon testing.

## Required Test Types

Every module must include:

1. Unit tests
2. Contract tests
3. Regression tests with golden fixtures
4. Integration tests through pipeline chains
5. Smoke performance tests for large inputs

## Regression Fixtures

Each regression fixture must include:

- input file or input JSON
- expected output JSON
- expected warnings
- expected confidence score range

Example:

```text
backend/tests/regression/fixtures/reference_extraction/
  input.txt
  expected_references.json
```

## LLM Testing

LLM modules must support fake deterministic responses.

Required:

- prompt contract tests
- citation presence tests
- no-unsupported-claim tests
- Serbian-language output tests

## Acceptance Gates

No module is complete until:

- unit tests pass
- contract tests pass
- at least one regression fixture exists
- docs mention public methods and config
- API schemas match `MASTER_INTERFACES.md`

## CI Phases

MVP CI:

```text
ruff/format later
python -m compileall backend
pytest backend/tests
```

Future CI:

```text
backend unit tests
backend contract tests
frontend typecheck
frontend component tests
docker build smoke
```

