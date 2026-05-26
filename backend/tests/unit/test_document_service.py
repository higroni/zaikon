"""Unit tests for the Documents service."""

from pathlib import Path

from zaikon.modules.documents.schemas import ExtractTextRequest
from zaikon.modules.documents.schemas import ClassifyDocumentRequest
from zaikon.modules.documents.service import DocumentService


FIXTURE_DIR = Path(__file__).parents[1] / "regression" / "fixtures" / "corpus_folder_import"


def test_document_service_extracts_text_from_txt_fixture():
    source_path = FIXTURE_DIR / "small_txt_corpus" / "zakon.txt"

    response = DocumentService().extract_text(
        ExtractTextRequest(
            source_uri=str(source_path),
            filename="zakon.txt",
            file_type="txt",
        )
    )

    assert response.document.extraction_status == "completed"
    assert response.document.metadata["character_count"] > 0
    assert "Zakon o primerima" in response.document.content_text


def test_document_service_extracts_text_from_pdf_fixture():
    source_path = FIXTURE_DIR / "small_txt_corpus" / "uredba.pdf"

    response = DocumentService().extract_text(
        ExtractTextRequest(
            source_uri=str(source_path),
            filename="uredba.pdf",
            file_type="pdf",
        )
    )

    assert response.document.extraction_status == "completed"
    assert response.document.metadata["page_count"] == 1
    assert "PDF tekst za regresioni test" in response.document.content_text


def test_document_service_extracts_text_from_docx_fixture():
    source_path = FIXTURE_DIR / "small_txt_corpus" / "pravilnik.docx"

    response = DocumentService().extract_text(
        ExtractTextRequest(
            source_uri=str(source_path),
            filename="pravilnik.docx",
            file_type="docx",
        )
    )

    assert response.document.extraction_status == "completed"
    assert response.document.metadata["paragraph_count"] == 3
    assert "DOCX tekst za regresioni test" in response.document.content_text


def test_document_service_classifies_serbian_document_types():
    service = DocumentService()
    examples = [
        ("ZAKON\no sumama", "zakon_o_sumama.pdf", "law"),
        ("UREDBA\no programu", "uredba_o_programu.pdf", "regulation"),
        ("PRAVILNIK\no obrascu", "pravilnik_o_obrascu.pdf", "rulebook"),
        ("NAREDBA\no merama", "naredba_mere.pdf", "order"),
        ("STRATEGIJA\nrazvoja", "strategija_razvoja.pdf", "strategy"),
        (
            "\u041f\u0420\u0410\u0412\u0418\u041b\u041d\u0418\u041a\n"
            "\u043e \u043e\u0431\u0440\u0430\u0441\u0446\u0443",
            "nepoznato.pdf",
            "rulebook",
        ),
        (
            "Na osnovu clana 68. stav 4. Zakona o sumama\n"
            "zakon)\n"
            "Ministar donosi\n"
            "PRAVILNIK\n"
            "o obrascu\n"
            "Clan 1.\n"
            "Ovim pravilnikom...",
            "pravilnik_o_obrascu.pdf",
            "rulebook",
        ),
        (
            "Na osnovu clana 68. stav 4. Zakona o sumama\n"
            "Ministar donosi\n"
            "PRAVILNIK\n"
            "o obrascu\n"
            "Clan 1.\n"
            "Ovim pravilnikom...",
            "zakon_o_obrascu.pdf",
            "rulebook",
        ),
        (
            "Na osnovu clana 45. Zakona o sumama\n"
            "Ministar donosi\n"
            "NAREDBU\n"
            "o merama\n"
            "1. Ovom naredbom...",
            "zakon_o_merama.pdf",
            "order",
        ),
    ]

    for content_text, filename, expected_document_type in examples:
        response = service.classify_document(
            ClassifyDocumentRequest(content_text=content_text, filename=filename)
        )

        assert response.document_type == expected_document_type
        assert response.confidence >= 0.65


def test_document_service_uses_filename_only_as_low_confidence_fallback():
    response = DocumentService().classify_document(
        ClassifyDocumentRequest(
            content_text="Neodredjen tekst bez naslovnog tipa akta.",
            filename="pravilnik_iz_naziva.pdf",
        )
    )

    assert response.document_type == "rulebook"
    assert response.confidence < 0.50
