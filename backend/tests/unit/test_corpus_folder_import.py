"""Unit and regression tests for corpus folder import."""

import json
from pathlib import Path

from zaikon.pipeline.steps.corpus.folder_import import (
    CorpusFolderImportChain,
    serbian_cyrillic_to_latin,
)


FIXTURE_DIR = Path(__file__).parents[1] / "regression" / "fixtures" / "corpus_folder_import"


def test_corpus_folder_import_chain_matches_regression_fixture():
    expected = json.loads((FIXTURE_DIR / "expected_import_report.json").read_text())
    corpus_dir = FIXTURE_DIR / "small_txt_corpus"

    context = CorpusFolderImportChain().run({"folder_uri": str(corpus_dir)})

    report = context.get_artifact("import_report").payload
    assert report["summary"] == expected["summary"]
    assert report["pipeline_run_id"] == str(context.pipeline_run_id)
    assert set(report["index_reports"]) == {
        "keyword",
        "vector",
        "structure",
        "reference_graph",
    }
    assert report["storage_report"]["metadata"]["stored_documents"] == 3

    supported = [
        item["filename"]
        for item in report["source_files"]
        if item["import_status"] == "completed"
    ]
    unsupported = [
        item["filename"]
        for item in report["source_files"]
        if item["import_status"] == "skipped"
    ]
    warning_codes = [warning["code"] for warning in report["warnings"]]

    assert supported == expected["supported_filenames"]
    assert unsupported == expected["unsupported_filenames"]
    assert warning_codes == expected["expected_warnings"]

    extracted_documents = context.get_artifact("extracted_documents").payload
    assert len(extracted_documents) == 3

    extracted_by_filename = {
        document["filename"]: document for document in extracted_documents
    }
    assert "Clan 1." in extracted_by_filename["zakon.txt"]["content_text"]
    assert "PDF tekst za regresioni test" in extracted_by_filename["uredba.pdf"][
        "content_text"
    ]
    assert "DOCX tekst za regresioni test" in extracted_by_filename["pravilnik.docx"][
        "content_text"
    ]

    normalized_documents = context.get_artifact("normalized_documents").payload
    normalized_by_filename = {
        document["filename"]: document for document in normalized_documents
    }
    normalized_txt = normalized_by_filename["zakon.txt"]
    assert "Član 4." in normalized_txt["content_text"]
    assert "Ljudska prava i javni interes štite se zakonom." in normalized_txt[
        "content_text"
    ]
    assert normalized_txt["metadata"]["normalization_applied"] is True
    assert normalized_txt["metadata"]["normalization"] == "sr_cyrillic_to_latin"

    identified_documents = context.get_artifact("identified_documents").payload
    identified_types = {
        document["filename"]: document["document_type"]
        for document in identified_documents
    }
    assert identified_types["zakon.txt"] == "law"
    assert identified_types["uredba.pdf"] == "regulation"
    assert identified_types["pravilnik.docx"] == "rulebook"

    parsed_documents = context.get_artifact("parsed_legal_documents").payload
    parsed_by_filename = {document["filename"]: document for document in parsed_documents}
    parsed_txt = parsed_by_filename["zakon.txt"]
    assert parsed_txt["document_type"] == "law"
    assert parsed_by_filename["uredba.pdf"]["document_type"] == "regulation"
    assert parsed_by_filename["pravilnik.docx"]["document_type"] == "rulebook"
    assert parsed_txt["metadata"]["section_count"] == 0
    assert parsed_txt["metadata"]["article_count"] == 2
    assert parsed_txt["metadata"]["paragraph_count"] == 2
    assert parsed_txt["metadata"]["item_count"] == 0
    assert [unit["number"] for unit in parsed_txt["legal_units"] if unit["unit_type"] == "article"] == [
        "1",
        "4",
    ]

    canonical_documents = context.get_artifact("canonical_documents").payload
    canonical_by_filename = {
        document["filename"]: document for document in canonical_documents
    }
    canonical_txt = canonical_by_filename["zakon.txt"]["canonical_json"]
    assert canonical_txt["schema_version"] == "0.1"
    assert canonical_txt["document"]["document_type"] == "law"
    assert canonical_txt["metadata"]["canonical_unit_count"] == len(
        parsed_txt["legal_units"]
    )

    extracted_references = context.get_artifact("extracted_references").payload
    assert {document["filename"] for document in extracted_references} == {
        "pravilnik.docx",
        "uredba.pdf",
        "zakon.txt",
    }
    assert all("reference_count" in document["metadata"] for document in extracted_references)

    resolved_references = context.get_artifact("resolved_references").payload
    assert {document["filename"] for document in resolved_references} == {
        "pravilnik.docx",
        "uredba.pdf",
        "zakon.txt",
    }
    assert all("resolved_count" in document["metadata"] for document in resolved_references)

    extracted_definitions = context.get_artifact("extracted_definitions").payload
    definitions_by_filename = {
        document["filename"]: document for document in extracted_definitions
    }
    zakon_definitions = definitions_by_filename["zakon.txt"]["definitions"]
    assert zakon_definitions[0]["term"] == "Ministarstvo"
    assert "Ministarstvo nadlezno" in zakon_definitions[0]["definition_text"]

    stored_documents_report = context.get_artifact("stored_documents_report").payload
    assert stored_documents_report["metadata"] == {
        "stored_documents": 3,
        "storage_backend": "in_memory_report",
    }
    assert {
        document["storage_status"]
        for document in stored_documents_report["stored_documents"]
    } == {"ready"}

    keyword_index_report = context.get_artifact("keyword_index_report").payload
    vector_index_report = context.get_artifact("vector_index_report").payload
    structure_index_report = context.get_artifact("structure_index_report").payload
    reference_graph_report = context.get_artifact("reference_graph_report").payload
    assert keyword_index_report["status"] == "completed"
    assert keyword_index_report["indexed_documents"] == 3
    assert vector_index_report["metadata"]["status_note"] == "report_only_no_embeddings_computed"
    assert structure_index_report["metadata"]["document_types"]["law"] == 1
    assert "resolved_references" in reference_graph_report["metadata"]


def test_serbian_cyrillic_to_latin_transliterates_digraphs():
    assert serbian_cyrillic_to_latin("Љубав Његош Џак") == "Ljubav Njegoš Džak"
    assert serbian_cyrillic_to_latin("љубав његош џак") == "ljubav njegoš džak"
