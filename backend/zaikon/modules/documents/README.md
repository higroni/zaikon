# Documents Module

Owns extraction and document classification.

Initial responsibilities:

- extract text from PDF
- extract text from DOCX
- read TXT
- preserve source metadata

Current MVP implementation:

- deterministic TXT, PDF, and DOCX extraction through `DocumentService.extract_text`
- lightweight heuristic classification through `DocumentService.classify_document`

