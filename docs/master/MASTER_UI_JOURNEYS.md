# MASTER_UI_JOURNEYS

This document is the golden copy for zAIkon user journeys.

## Journey 1: Corpus Folder Import

1. User opens `Corpus`.
2. User creates or selects a corpus.
3. User starts `New Folder Import`.
4. User chooses:
   - local folder path or browser folder upload
   - language
   - domain
   - recursive import
   - skip duplicates
   - build indexes
5. System shows import progress by file and step.
6. System shows import report.
7. User reviews parsing warnings.

## Journey 2: Corpus Explorer

1. User opens a corpus.
2. User searches laws and regulations.
3. User opens a document.
4. UI shows tree:
   - document
   - article
   - paragraph
   - item
5. UI shows references and graph preview.

## Journey 3: Draft Compliance Review

1. User uploads draft law.
2. System parses draft.
3. User reviews parsing preview.
4. User selects corpus and checker suite.
5. User runs review.
6. System shows progress by module.
7. UI opens findings table.

## Journey 4: Finding Review

1. User opens a finding.
2. UI shows:
   - draft provision
   - relevant existing provision
   - evidence quote
   - explanation
   - recommendation
3. User marks finding:
   - accepted
   - rejected
   - partial
   - needs expert review
4. User adds comment.

## Journey 5: AI Assistant

1. User opens assistant in context of a draft review.
2. User asks a Serbian-language question.
3. System parses intent.
4. System retrieves cited sources.
5. Assistant answers in Serbian with citations.
6. User asks for a suggested revision.
7. Assistant generates a suggested legal formulation with cited basis.

## Journey 6: Report Export

1. User selects findings.
2. User generates report.
3. User downloads DOCX/PDF.

