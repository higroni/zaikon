# References Module

Owns reference extraction and resolution.

Current MVP implementation:

- extracts normalized Latin article references such as `clan 5. stav 2.`
- extracts `Sluzbeni glasnik RS` references
- leaves cross-document resolution for the next slice.
- resolves article, paragraph, and item references within the same canonical
  document when the reference includes `clan`, optional `stav`, and optional
  `tacka`

Examples:

- `član 5.`
- `član 5. stav 2.`
- `zakon kojim se uređuje ...`
- `izuzetno od člana ...`

