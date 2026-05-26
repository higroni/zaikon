# Legal Parser Module

Owns Serbian and Macedonian legal structure parsing.

Initial Serbian units:

- document
- article
- paragraph
- item
- subitem
- transitional provision
- final provision

Current MVP implementation:

- parses normalized Serbian Latin text
- detects article headers matching `Clan N.` / `Član N.`
- emits article, paragraph, inline item, and inline subitem `ParsedLegalUnit`
  records

