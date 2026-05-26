# Canonical Module

Owns conversion to internal canonical JSON and later Akoma Ntoso XML
import/export.

Runtime canonical format is JSON. XML is interoperability format.

Current MVP implementation:

- converts `ParsedLegalDocument` to `CanonicalDocument`
- preserves legal unit hierarchy fields required for storage, indexing, and
  later Akoma Ntoso export

