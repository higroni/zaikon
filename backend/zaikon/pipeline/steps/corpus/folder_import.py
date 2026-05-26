"""Corpus folder import pipeline steps."""

from hashlib import sha256
from pathlib import Path
import re
from urllib.parse import unquote, urlparse
from uuid import NAMESPACE_URL, uuid4, uuid5

from zaikon.core.config import settings
from zaikon.modules.canonical.schemas import CanonicalizeRequest
from zaikon.modules.canonical.schemas import CanonicalDocument
from zaikon.modules.canonical.service import get_canonical_service
from zaikon.modules.documents.schemas import ClassifyDocumentRequest
from zaikon.modules.documents.schemas import ExtractTextRequest
from zaikon.modules.documents.service import get_document_service
from zaikon.modules.indexing.schemas import BuildIndexesRequest
from zaikon.modules.indexing.service import get_indexing_service
from zaikon.modules.legal_parser.schemas import ParsedLegalDocument
from zaikon.modules.legal_parser.schemas import ParseLegalStructureRequest
from zaikon.modules.legal_parser.service import get_legal_parser_service
from zaikon.modules.references.schemas import ExtractReferencesRequest
from zaikon.modules.references.schemas import LegalReferenceRecord
from zaikon.modules.references.schemas import ResolveReferencesRequest
from zaikon.modules.references.service import get_reference_service
from zaikon.modules.storage.sqlite_store import SQLiteDocumentStore
from zaikon.pipeline.base import PipelineStep
from zaikon.pipeline.chains import PipelineChain
from zaikon.pipeline.context import PipelineContext


def _path_from_uri(source_uri: str) -> Path:
    if source_uri.startswith("file://"):
        parsed = urlparse(source_uri)
        path = unquote(parsed.path)
        if re.match(r"^/[A-Za-z]:/", path):
            path = path[1:]
        if parsed.netloc:
            path = f"//{parsed.netloc}{path}"
        return Path(path)
    return Path(source_uri)


def _file_uri(path: Path) -> str:
    return path.resolve().as_uri()


_CYRILLIC_TO_LATIN = {
    "А": "A",
    "Б": "B",
    "В": "V",
    "Г": "G",
    "Д": "D",
    "Ђ": "Đ",
    "Е": "E",
    "Ж": "Ž",
    "З": "Z",
    "И": "I",
    "Ј": "J",
    "К": "K",
    "Л": "L",
    "Љ": "Lj",
    "М": "M",
    "Н": "N",
    "Њ": "Nj",
    "О": "O",
    "П": "P",
    "Р": "R",
    "С": "S",
    "Т": "T",
    "Ћ": "Ć",
    "У": "U",
    "Ф": "F",
    "Х": "H",
    "Ц": "C",
    "Ч": "Č",
    "Џ": "Dž",
    "Ш": "Š",
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "ђ": "đ",
    "е": "e",
    "ж": "ž",
    "з": "z",
    "и": "i",
    "ј": "j",
    "к": "k",
    "л": "l",
    "љ": "lj",
    "м": "m",
    "н": "n",
    "њ": "nj",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "ћ": "ć",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "c",
    "ч": "č",
    "џ": "dž",
    "ш": "š",
}


def serbian_cyrillic_to_latin(text: str) -> str:
    return "".join(_CYRILLIC_TO_LATIN.get(character, character) for character in text)


class ScanFolderStep(PipelineStep):
    step_name = "scan_folder"
    produces = ("source_file_manifest",)

    def run(self, context: PipelineContext) -> PipelineContext:
        folder_uri = context.inputs["folder_uri"]
        recursive = context.inputs.get("recursive")
        if recursive is None:
            recursive = settings.import_recursive

        folder_path = _path_from_uri(folder_uri)
        if not folder_path.exists() or not folder_path.is_dir():
            raise FileNotFoundError(f"Folder not found: {folder_uri}")

        iterator = folder_path.rglob("*") if recursive else folder_path.glob("*")
        files = sorted(path for path in iterator if path.is_file())
        manifest = [
            {
                "source_uri": _file_uri(path),
                "filename": path.name,
                "suffix": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
            }
            for path in files
        ]

        context.add_artifact(
            self.artifact(
                name="source_file_manifest",
                artifact_type="source_file_manifest",
                payload=manifest,
            )
        )
        context.log("INFO", f"Scanned {len(manifest)} source files", self.step_name)
        return context


class DetectFileTypesStep(PipelineStep):
    step_name = "detect_file_types"
    requires = ("source_file_manifest",)
    produces = ("import_report",)

    def run(self, context: PipelineContext) -> PipelineContext:
        manifest = context.get_artifact("source_file_manifest")
        allowed_extensions = settings.allowed_extensions
        source_files = []
        warnings = []
        seen_hashes: dict[str, str] = {}
        duplicate_files = 0

        for item in manifest.payload:
            path = _path_from_uri(item["source_uri"])
            suffix = item["suffix"]
            supported = suffix in allowed_extensions
            file_type = suffix.removeprefix(".") if suffix else "unknown"
            content_hash = sha256(path.read_bytes()).hexdigest()
            is_duplicate = (
                settings.import_skip_duplicates
                and supported
                and content_hash in seen_hashes
            )
            source_file = {
                "source_uri": item["source_uri"],
                "filename": item["filename"],
                "file_type": file_type,
                "content_hash": content_hash,
                "size_bytes": item["size_bytes"],
                "import_status": "pending"
                if supported and not is_duplicate
                else "skipped",
                "error_message": self._skip_reason(supported, is_duplicate),
            }
            source_files.append(source_file)
            if supported and not is_duplicate:
                seen_hashes[content_hash] = item["source_uri"]
            if not supported:
                warnings.append(
                    {
                        "code": "unsupported_file_type",
                        "message": f"Unsupported file type: {item['filename']}",
                        "source_uri": item["source_uri"],
                    }
                )
            if is_duplicate:
                duplicate_files += 1
                warnings.append(
                    {
                        "code": "duplicate_file",
                        "message": f"Duplicate source file skipped: {item['filename']}",
                        "source_uri": item["source_uri"],
                        "duplicate_of": seen_hashes[content_hash],
                    }
                )

        summary = {
            "total_files": len(source_files),
            "supported_files": sum(
                1 for item in source_files if item["import_status"] == "pending"
            ),
            "unsupported_files": sum(
                1
                for item in source_files
                if item["error_message"] == "unsupported_file_type"
            ),
        }
        if duplicate_files:
            summary["duplicate_files"] = duplicate_files
        context.add_artifact(
            self.artifact(
                name="import_report",
                artifact_type="import_report",
                payload={
                    "source_files": source_files,
                    "warnings": warnings,
                    "summary": summary,
                },
            )
        )
        context.log(
            "INFO",
            f"Detected {summary['supported_files']} supported source files",
            self.step_name,
        )
        return context

    def _skip_reason(self, supported: bool, is_duplicate: bool) -> str | None:
        if is_duplicate:
            return "duplicate_file"
        if not supported:
            return "unsupported_file_type"
        return None


class ExtractTextStep(PipelineStep):
    step_name = "extract_text"
    requires = ("import_report",)
    produces = ("extracted_documents", "import_report")

    def run(self, context: PipelineContext) -> PipelineContext:
        report = context.get_artifact("import_report")
        document_service = get_document_service()
        extracted_documents = []
        source_files = []

        for source_file in report.payload["source_files"]:
            if source_file["import_status"] != "pending":
                source_files.append(source_file)
                continue

            try:
                response = document_service.extract_text(
                    ExtractTextRequest(
                        source_uri=source_file["source_uri"],
                        filename=source_file["filename"],
                        file_type=source_file["file_type"],
                    )
                )
                extracted_documents.append(response.document.model_dump(mode="json"))
                source_file = {
                    **source_file,
                    "import_status": "completed",
                    "error_message": None,
                }
            except Exception as exc:
                source_file = {
                    **source_file,
                    "import_status": "failed",
                    "error_message": str(exc),
                }
            source_files.append(source_file)

        summary = {
            **report.payload["summary"],
            "extracted_documents": len(extracted_documents),
            "failed_files": sum(
                1 for item in source_files if item["import_status"] == "failed"
            ),
        }
        updated_report = {
            **report.payload,
            "source_files": source_files,
            "summary": summary,
        }
        context.add_artifact(
            self.artifact(
                name="extracted_documents",
                artifact_type="extracted_documents",
                payload=extracted_documents,
            )
        )
        context.add_artifact(
            self.artifact(
                name="import_report",
                artifact_type="import_report",
                payload=updated_report,
            )
        )
        context.log(
            "INFO",
            f"Extracted text from {len(extracted_documents)} source files",
            self.step_name,
        )
        return context


class NormalizeTextStep(PipelineStep):
    step_name = "normalize_text"
    requires = ("extracted_documents",)
    produces = ("extracted_documents", "normalized_documents")

    def run(self, context: PipelineContext) -> PipelineContext:
        extracted = context.get_artifact("extracted_documents")
        normalized_documents = []
        enabled = settings.enable_cyrillic_latin_normalization

        for document in extracted.payload:
            content_text = document["content_text"]
            normalized_text = (
                serbian_cyrillic_to_latin(content_text) if enabled else content_text
            )
            normalized_documents.append(
                {
                    **document,
                    "content_text": normalized_text,
                    "metadata": {
                        **document.get("metadata", {}),
                        "normalization_applied": enabled
                        and normalized_text != content_text,
                        "normalization": (
                            "sr_cyrillic_to_latin" if enabled else "none"
                        ),
                    },
                }
            )

        context.add_artifact(
            self.artifact(
                name="normalized_documents",
                artifact_type="normalized_documents",
                payload=normalized_documents,
            )
        )
        context.add_artifact(
            self.artifact(
                name="extracted_documents",
                artifact_type="extracted_documents",
                payload=normalized_documents,
            )
        )
        context.log(
            "INFO",
            f"Normalized {len(normalized_documents)} extracted documents",
            self.step_name,
        )
        return context


class IdentifyLegalDocumentsStep(PipelineStep):
    step_name = "identify_legal_documents"
    requires = ("extracted_documents", "import_report")
    produces = ("identified_documents", "extracted_documents", "import_report")

    def run(self, context: PipelineContext) -> PipelineContext:
        extracted = context.get_artifact("extracted_documents")
        import_report = context.get_artifact("import_report")
        document_service = get_document_service()
        identified_documents = []
        classification_by_source_uri = {}

        for document in extracted.payload:
            classification = document_service.classify_document(
                ClassifyDocumentRequest(
                    content_text=document["content_text"],
                    filename=document["filename"],
                    language_code=document["language_code"],
                )
            )
            identified_documents.append(
                {
                    **document,
                    "document_type": classification.document_type,
                    "metadata": {
                        **document.get("metadata", {}),
                        "document_type": classification.document_type,
                        "document_type_confidence": classification.confidence,
                        "publication_metadata": classification.metadata,
                    },
                }
            )
            classification_by_source_uri[document["source_uri"]] = classification

        context.add_artifact(
            self.artifact(
                name="identified_documents",
                artifact_type="identified_documents",
                payload=identified_documents,
            )
        )
        context.add_artifact(
            self.artifact(
                name="extracted_documents",
                artifact_type="extracted_documents",
                payload=identified_documents,
            )
        )
        context.add_artifact(
            self.artifact(
                name="import_report",
                artifact_type="import_report",
                payload={
                    **import_report.payload,
                    "summary": {
                        **import_report.payload["summary"],
                        "document_types": self._document_type_counts(
                            classification_by_source_uri.values()
                        ),
                    },
                    "source_files": [
                        {
                            **source_file,
                            "document_type": classification_by_source_uri[
                                source_file["source_uri"]
                            ].document_type,
                            "document_type_confidence": classification_by_source_uri[
                                source_file["source_uri"]
                            ].confidence,
                            "publication_metadata": classification_by_source_uri[
                                source_file["source_uri"]
                            ].metadata,
                        }
                        if source_file["source_uri"] in classification_by_source_uri
                        else source_file
                        for source_file in import_report.payload["source_files"]
                    ],
                },
            )
        )
        context.log(
            "INFO",
            f"Identified {len(identified_documents)} legal documents",
            self.step_name,
        )
        return context

    def _document_type_counts(self, classifications) -> dict[str, int]:
        counts: dict[str, int] = {}
        for classification in classifications:
            counts[classification.document_type] = (
                counts.get(classification.document_type, 0) + 1
            )
        return counts


class ParseLegalStructureStep(PipelineStep):
    step_name = "parse_legal_structure"
    requires = ("extracted_documents",)
    produces = ("parsed_legal_documents",)

    def run(self, context: PipelineContext) -> PipelineContext:
        extracted = context.get_artifact("extracted_documents")
        parser_service = get_legal_parser_service()
        parsed_documents = []

        for document in extracted.payload:
            response = parser_service.parse_legal_structure(
                ParseLegalStructureRequest(
                    source_uri=document["source_uri"],
                    filename=document["filename"],
                    content_text=document["content_text"],
                    document_type=document.get("document_type", "unknown"),
                    language_code=document["language_code"],
                )
            )
            parsed_documents.append(response.document.model_dump(mode="json"))

        context.add_artifact(
            self.artifact(
                name="parsed_legal_documents",
                artifact_type="parsed_legal_documents",
                payload=parsed_documents,
            )
        )
        context.log(
            "INFO",
            f"Parsed legal structure for {len(parsed_documents)} documents",
            self.step_name,
        )
        return context


class ConvertToCanonicalJsonStep(PipelineStep):
    step_name = "convert_to_canonical_json"
    requires = ("parsed_legal_documents",)
    produces = ("canonical_documents",)

    def run(self, context: PipelineContext) -> PipelineContext:
        parsed_artifact = context.get_artifact("parsed_legal_documents")
        canonical_service = get_canonical_service()
        canonical_documents = []

        for document in parsed_artifact.payload:
            parsed_document = ParsedLegalDocument.model_validate(document)
            response = canonical_service.to_canonical_json(
                CanonicalizeRequest(document=parsed_document)
            )
            canonical_documents.append(response.document.model_dump(mode="json"))

        context.add_artifact(
            self.artifact(
                name="canonical_documents",
                artifact_type="canonical_documents",
                payload=canonical_documents,
            )
        )
        context.log(
            "INFO",
            f"Converted {len(canonical_documents)} documents to canonical JSON",
            self.step_name,
        )
        return context


class ExtractReferencesStep(PipelineStep):
    step_name = "extract_references"
    requires = ("canonical_documents",)
    produces = ("extracted_references",)

    def run(self, context: PipelineContext) -> PipelineContext:
        canonical_artifact = context.get_artifact("canonical_documents")
        reference_service = get_reference_service()
        extracted_references = []

        for document in canonical_artifact.payload:
            canonical_document = CanonicalDocument.model_validate(document)
            response = reference_service.extract_references(
                ExtractReferencesRequest(document=canonical_document)
            )
            extracted_references.append(
                {
                    "source_uri": canonical_document.source_uri,
                    "filename": canonical_document.filename,
                    "references": [
                        reference.model_dump(mode="json")
                        for reference in response.references
                    ],
                    "metadata": {"reference_count": len(response.references)},
                }
            )

        context.add_artifact(
            self.artifact(
                name="extracted_references",
                artifact_type="extracted_references",
                payload=extracted_references,
            )
        )
        context.log(
            "INFO",
            f"Extracted references from {len(extracted_references)} documents",
            self.step_name,
        )
        return context


class ResolveReferencesStep(PipelineStep):
    step_name = "resolve_references"
    requires = ("canonical_documents", "extracted_references")
    produces = ("resolved_references",)

    def run(self, context: PipelineContext) -> PipelineContext:
        canonical_documents = {
            document["source_uri"]: CanonicalDocument.model_validate(document)
            for document in context.get_artifact("canonical_documents").payload
        }
        extracted_references = context.get_artifact("extracted_references").payload
        reference_service = get_reference_service()
        resolved_documents = []

        for document_references in extracted_references:
            canonical_document = canonical_documents[document_references["source_uri"]]
            references = [
                LegalReferenceRecord.model_validate(reference)
                for reference in document_references["references"]
            ]
            response = reference_service.resolve_references(
                ResolveReferencesRequest(
                    references=references,
                    document=canonical_document,
                )
            )
            resolved_documents.append(
                {
                    "source_uri": canonical_document.source_uri,
                    "filename": canonical_document.filename,
                    "resolved_references": [
                        item.model_dump(mode="json")
                        for item in response.resolved_references
                    ],
                    "metadata": {
                        "resolved_count": sum(
                            1
                            for item in response.resolved_references
                            if item.resolution_status == "resolved"
                        ),
                        "missing_count": sum(
                            1
                            for item in response.resolved_references
                            if item.resolution_status == "missing"
                        ),
                        "out_of_scope_count": sum(
                            1
                            for item in response.resolved_references
                            if item.resolution_status == "out_of_scope"
                        ),
                    },
                }
            )

        context.add_artifact(
            self.artifact(
                name="resolved_references",
                artifact_type="resolved_references",
                payload=resolved_documents,
            )
        )
        context.log(
            "INFO",
            f"Resolved references for {len(resolved_documents)} documents",
            self.step_name,
        )
        return context


_DALJEM_TEKSTU_RE = re.compile(
    r"(?P<definition_text>[^.()]{3,120}?)\s*\(u\s+daljem\s+tekstu:\s*"
    r"(?P<term>[^)]+)\)",
    re.IGNORECASE,
)


class ExtractDefinitionsStep(PipelineStep):
    step_name = "extract_definitions"
    requires = ("canonical_documents",)
    produces = ("extracted_definitions",)

    def run(self, context: PipelineContext) -> PipelineContext:
        extracted_definitions = []
        for document in context.get_artifact("canonical_documents").payload:
            definitions = []
            for unit in document["canonical_json"].get("legal_units", []):
                content_text = unit.get("content_text") or ""
                for match in _DALJEM_TEKSTU_RE.finditer(content_text):
                    term = match.group("term").strip(" :;,.")
                    definition_text = match.group("definition_text").strip(" :;,.")
                    definitions.append(
                        {
                            "definition_id": str(uuid4()),
                            "source_legal_unit_id": unit.get("legal_unit_id"),
                            "source_path": unit.get("path"),
                            "term": term,
                            "definition_text": definition_text,
                            "confidence": 0.78,
                        }
                    )
            extracted_definitions.append(
                {
                    "source_uri": document["source_uri"],
                    "filename": document["filename"],
                    "definitions": definitions,
                    "metadata": {"definition_count": len(definitions)},
                }
            )

        context.add_artifact(
            self.artifact(
                name="extracted_definitions",
                artifact_type="extracted_definitions",
                payload=extracted_definitions,
            )
        )
        context.log(
            "INFO",
            f"Extracted definitions from {len(extracted_definitions)} documents",
            self.step_name,
        )
        return context


class StoreDocumentsStep(PipelineStep):
    step_name = "store_documents"
    requires = ("canonical_documents", "import_report")
    produces = ("stored_documents_report", "import_report")

    def run(self, context: PipelineContext) -> PipelineContext:
        canonical_documents = context.get_artifact("canonical_documents").payload
        import_report = context.get_artifact("import_report")
        source_files_by_uri = {
            source_file["source_uri"]: source_file
            for source_file in import_report.payload["source_files"]
        }
        stored_documents = [
            {
                "document_id": str(uuid5(NAMESPACE_URL, document["source_uri"])),
                "corpus_id": context.inputs.get("corpus_id"),
                "source_uri": document["source_uri"],
                "filename": document["filename"],
                "document_type": document["document_type"],
                "title": document["title"],
                "canonical_unit_count": document["canonical_json"]["metadata"][
                    "canonical_unit_count"
                ],
                "publication_metadata": source_files_by_uri.get(
                    document["source_uri"], {}
                ).get("publication_metadata", {}),
                "storage_status": "ready",
            }
            for document in canonical_documents
        ]
        self._mirror_to_sqlite(stored_documents, canonical_documents)
        stored_documents_report = {
            "stored_documents": stored_documents,
            "metadata": {
                "stored_documents": len(stored_documents),
                "storage_backend": "in_memory_report",
            },
        }
        updated_report = {
            **import_report.payload,
            "summary": {
                **import_report.payload["summary"],
                "stored_documents": len(stored_documents),
            },
        }

        context.add_artifact(
            self.artifact(
                name="stored_documents_report",
                artifact_type="stored_documents_report",
                payload=stored_documents_report,
            )
        )
        context.add_artifact(
            self.artifact(
                name="import_report",
                artifact_type="import_report",
                payload=updated_report,
            )
        )
        context.log(
            "INFO",
            f"Prepared {len(stored_documents)} canonical documents for storage",
            self.step_name,
        )
        return context

    def _mirror_to_sqlite(
        self, stored_documents: list[dict], canonical_documents: list[dict]
    ) -> None:
        if not settings.database_url.startswith("sqlite:///"):
            return
        database_path = settings.database_url.removeprefix("sqlite:///")
        store = SQLiteDocumentStore(database_path)
        canonical_by_source_uri = {
            document["source_uri"]: document["canonical_json"]
            for document in canonical_documents
        }
        for record in stored_documents:
            store.upsert_document(
                record=record,
                canonical_json=canonical_by_source_uri.get(record["source_uri"], {}),
            )


class _BaseIndexReportStep(PipelineStep):
    requires = ("canonical_documents", "resolved_references")

    def _build_index_reports(self, context: PipelineContext):
        documents = [
            CanonicalDocument.model_validate(document)
            for document in context.get_artifact("canonical_documents").payload
        ]
        resolved_references = context.get_artifact("resolved_references").payload
        return get_indexing_service().build_indexes(
            BuildIndexesRequest(
                documents=documents,
                resolved_references=resolved_references,
            )
        )


class BuildKeywordIndexStep(_BaseIndexReportStep):
    step_name = "build_keyword_index"
    produces = ("keyword_index_report",)

    def run(self, context: PipelineContext) -> PipelineContext:
        report = self._build_index_reports(context).keyword_index_report
        context.add_artifact(
            self.artifact(
                name="keyword_index_report",
                artifact_type="keyword_index_report",
                payload=report.model_dump(mode="json"),
            )
        )
        return context


class BuildVectorIndexStep(_BaseIndexReportStep):
    step_name = "build_vector_index"
    produces = ("vector_index_report",)

    def run(self, context: PipelineContext) -> PipelineContext:
        report = self._build_index_reports(context).vector_index_report
        context.add_artifact(
            self.artifact(
                name="vector_index_report",
                artifact_type="vector_index_report",
                payload=report.model_dump(mode="json"),
            )
        )
        return context


class BuildStructureIndexStep(_BaseIndexReportStep):
    step_name = "build_structure_index"
    produces = ("structure_index_report",)

    def run(self, context: PipelineContext) -> PipelineContext:
        report = self._build_index_reports(context).structure_index_report
        context.add_artifact(
            self.artifact(
                name="structure_index_report",
                artifact_type="structure_index_report",
                payload=report.model_dump(mode="json"),
            )
        )
        return context


class BuildReferenceGraphStep(_BaseIndexReportStep):
    step_name = "build_reference_graph"
    produces = ("reference_graph_report",)

    def run(self, context: PipelineContext) -> PipelineContext:
        report = self._build_index_reports(context).reference_graph_report
        context.add_artifact(
            self.artifact(
                name="reference_graph_report",
                artifact_type="reference_graph_report",
                payload=report.model_dump(mode="json"),
            )
        )
        return context


class GenerateImportReportStep(PipelineStep):
    step_name = "generate_import_report"
    requires = (
        "import_report",
        "stored_documents_report",
        "keyword_index_report",
        "vector_index_report",
        "structure_index_report",
        "reference_graph_report",
    )
    produces = ("import_report",)

    def run(self, context: PipelineContext) -> PipelineContext:
        import_report = context.get_artifact("import_report")
        finalized_report = {
            **import_report.payload,
            "index_reports": {
                "keyword": context.get_artifact("keyword_index_report").payload,
                "vector": context.get_artifact("vector_index_report").payload,
                "structure": context.get_artifact("structure_index_report").payload,
                "reference_graph": context.get_artifact("reference_graph_report").payload,
            },
            "storage_report": context.get_artifact("stored_documents_report").payload,
            "pipeline_run_id": str(context.pipeline_run_id),
        }
        context.add_artifact(
            self.artifact(
                name="import_report",
                artifact_type="import_report",
                payload=finalized_report,
            )
        )
        context.log("INFO", "Generated final import report", self.step_name)
        return context


class CorpusFolderImportChain(PipelineChain):
    def __init__(self) -> None:
        super().__init__(
            chain_name="CorpusFolderImportChain",
            steps=[
                ScanFolderStep(),
                DetectFileTypesStep(),
                ExtractTextStep(),
                NormalizeTextStep(),
                IdentifyLegalDocumentsStep(),
                ParseLegalStructureStep(),
                ConvertToCanonicalJsonStep(),
                ExtractReferencesStep(),
                ResolveReferencesStep(),
                ExtractDefinitionsStep(),
                StoreDocumentsStep(),
                BuildKeywordIndexStep(),
                BuildVectorIndexStep(),
                BuildStructureIndexStep(),
                BuildReferenceGraphStep(),
                GenerateImportReportStep(),
            ],
        )
