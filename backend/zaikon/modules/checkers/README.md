# Checkers Module

Owns compliance checker suite.

MVP checkers:

- ReferenceChecker
- DefinitionConsistencyChecker
- TerminologyChecker
- TemporalValidityChecker

Implemented MVP:

- `ReferenceChecker.check(...)` creates `reference_missing` findings when an
  extracted internal article reference cannot be resolved in the canonical draft.
- `DefinitionConsistencyChecker.check(...)` creates `definition_conflict`
  findings when the same term is defined with different wording in the draft.

