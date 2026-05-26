"""Unit tests for the Serbian legal parser."""

from zaikon.modules.legal_parser.schemas import ParseLegalStructureRequest
from zaikon.modules.legal_parser.service import LegalParserService


def test_legal_parser_extracts_articles_and_paragraphs():
    content_text = """Zakon o primerima

Clan 1.
Prvi pasus prvog clana.

Drugi pasus prvog clana.

Član 2.
Jedini pasus drugog clana.
"""

    response = LegalParserService().parse_legal_structure(
        ParseLegalStructureRequest(
            source_uri="file:///tmp/zakon.txt",
            filename="zakon.txt",
            content_text=content_text,
            document_type="law",
        )
    )

    document = response.document
    assert document.document_type == "law"
    assert document.title == "Zakon o primerima"
    assert document.metadata == {
        "section_count": 0,
        "article_count": 2,
        "paragraph_count": 3,
        "item_count": 0,
    }

    articles = [unit for unit in document.legal_units if unit.unit_type == "article"]
    paragraphs = [
        unit for unit in document.legal_units if unit.unit_type == "paragraph"
    ]

    assert [article.number for article in articles] == ["1", "2"]
    assert articles[0].path == "article:1"
    assert paragraphs[0].path == "article:1/paragraph:1"
    assert paragraphs[0].parent_legal_unit_id == articles[0].legal_unit_id


def test_legal_parser_extracts_sections_and_article_headings():
    content_text = """PRAVILNIK
o primerima

I. UVODNE ODREDBE

Predmet pravilnika
Clan 1.
Ovim pravilnikom uredjuje se primer.
"""

    response = LegalParserService().parse_legal_structure(
        ParseLegalStructureRequest(
            source_uri="file:///tmp/pravilnik.txt",
            filename="pravilnik.txt",
            content_text=content_text,
            document_type="rulebook",
        )
    )

    document = response.document
    sections = [unit for unit in document.legal_units if unit.unit_type == "section"]
    articles = [unit for unit in document.legal_units if unit.unit_type == "article"]

    assert document.document_type == "rulebook"
    assert sections[0].number == "I"
    assert sections[0].heading == "UVODNE ODREDBE"
    assert articles[0].heading == "Predmet pravilnika"
    assert document.metadata["section_count"] == 1


def test_legal_parser_extracts_numbered_items_when_document_has_no_articles():
    content_text = """NAREDBA
o merama zastite

1. Ovom naredbom odredjuju se mere zastite.
2. Radi zastite preduzimaju se sledece mere:
1) prvi podkorak ostaje u sadrzaju stavke za MVP.
"""

    response = LegalParserService().parse_legal_structure(
        ParseLegalStructureRequest(
            source_uri="file:///tmp/naredba.txt",
            filename="naredba.txt",
            content_text=content_text,
            document_type="order",
        )
    )

    document = response.document
    items = [unit for unit in document.legal_units if unit.unit_type == "item"]

    assert document.document_type == "order"
    assert document.metadata["article_count"] == 0
    assert document.metadata["item_count"] == 2
    assert [item.number for item in items] == ["1", "2"]
    assert "prvi podkorak" in items[1].content_text


def test_legal_parser_extracts_inline_items_inside_article_paragraph():
    content_text = """Zakon o tackama

Clan 1.
U postupku se obezbedjuje: 1) prvi uslov; 2) drugi uslov.
"""

    response = LegalParserService().parse_legal_structure(
        ParseLegalStructureRequest(
            source_uri="file:///tmp/zakon.txt",
            filename="zakon.txt",
            content_text=content_text,
            document_type="law",
        )
    )

    document = response.document
    paragraphs = [
        unit for unit in document.legal_units if unit.unit_type == "paragraph"
    ]
    items = [unit for unit in document.legal_units if unit.unit_type == "item"]

    assert document.metadata["item_count"] == 2
    assert [item.number for item in items] == ["1", "2"]
    assert items[0].parent_legal_unit_id == paragraphs[0].legal_unit_id
    assert items[0].path == "article:1/paragraph:1/item:1"
    assert items[1].content_text == "drugi uslov."
