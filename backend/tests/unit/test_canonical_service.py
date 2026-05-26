"""Unit tests for canonical JSON conversion."""

import xml.etree.ElementTree as ET

from zaikon.modules.canonical.schemas import (
    CanonicalizeRequest,
    ExportAkomaNtosoRequest,
    ImportAkomaNtosoRequest,
)
from zaikon.modules.canonical.service import CanonicalService
from zaikon.modules.legal_parser.schemas import ParsedLegalDocument, ParsedLegalUnit


def test_canonical_service_preserves_document_and_legal_units():
    article = ParsedLegalUnit(
        unit_type="article",
        number="1",
        ordinal=1,
        heading="Predmet",
        content_text="Ovim zakonom uredjuje se primer.",
        path="article:1",
    )
    paragraph = ParsedLegalUnit(
        parent_legal_unit_id=article.legal_unit_id,
        unit_type="paragraph",
        number="1",
        ordinal=1,
        heading=None,
        content_text="Ovim zakonom uredjuje se primer.",
        path="article:1/paragraph:1",
    )
    parsed = ParsedLegalDocument(
        source_uri="file:///tmp/zakon.txt",
        filename="zakon.txt",
        document_type="law",
        title="Zakon o primerima",
        legal_units=[article, paragraph],
        metadata={"article_count": 1, "paragraph_count": 1},
    )

    response = CanonicalService().to_canonical_json(
        CanonicalizeRequest(document=parsed)
    )

    canonical_json = response.document.canonical_json
    assert response.document.document_type == "law"
    assert canonical_json["schema_version"] == "0.1"
    assert canonical_json["document"]["title"] == "Zakon o primerima"
    assert canonical_json["legal_units"][0]["path"] == "article:1"
    assert canonical_json["legal_units"][1]["parent_legal_unit_id"] == str(
        article.legal_unit_id
    )
    assert canonical_json["metadata"]["canonical_unit_count"] == 2


def test_canonical_service_exports_basic_akoma_ntoso_xml():
    article = ParsedLegalUnit(
        unit_type="article",
        number="1",
        ordinal=1,
        heading="Predmet",
        content_text="Ovim zakonom uredjuje se primer.",
        path="article:1",
    )
    paragraph = ParsedLegalUnit(
        parent_legal_unit_id=article.legal_unit_id,
        unit_type="paragraph",
        number="1",
        ordinal=1,
        content_text="Ovim zakonom uredjuje se primer.",
        path="article:1/paragraph:1",
    )
    parsed = ParsedLegalDocument(
        source_uri="file:///tmp/zakon.txt",
        filename="zakon.txt",
        document_type="law",
        title="Zakon o primerima",
        legal_units=[article, paragraph],
    )
    service = CanonicalService()
    canonical = service.to_canonical_json(CanonicalizeRequest(document=parsed))

    response = service.export_akoma_ntoso(
        ExportAkomaNtosoRequest(document=canonical.document)
    )

    root = ET.fromstring(response.xml_text)
    namespace = {"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"}
    assert root.tag.endswith("akomaNtoso")
    assert root.find(".//akn:FRBRcountry", namespace).attrib["value"] == "rs"
    assert root.find(".//akn:FRBRlanguage", namespace).attrib["language"] == "srp"
    article_node = root.find(".//akn:article", namespace)
    assert article_node is not None
    assert article_node.attrib["eId"] == "article_1"
    assert article_node.find("akn:num", namespace).text == "Clan 1."
    assert root.find(".//akn:paragraph/akn:content/akn:p", namespace).text == (
        "Ovim zakonom uredjuje se primer."
    )


def test_canonical_service_imports_basic_akoma_ntoso_xml():
    xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act name="law">
    <meta>
      <identification source="#test">
        <FRBRWork>
          <FRBRuri value="/akn/rs/act/zakon-o-sumama"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRlanguage language="srp"/>
        </FRBRExpression>
      </identification>
    </meta>
    <body>
      <article eId="art_1">
        <num>Clan 1.</num>
        <heading>Predmet</heading>
        <paragraph eId="art_1_para_1">
          <num>(1)</num>
          <content>
            <p>Šume su dobro od opšteg interesa.</p>
          </content>
        </paragraph>
      </article>
    </body>
  </act>
</akomaNtoso>
"""

    response = CanonicalService().import_akoma_ntoso(
        ImportAkomaNtosoRequest(
            xml_text=xml_text,
            source_uri="file:///tmp/zakon.xml",
            filename="zakon.xml",
        )
    )

    document = response.document
    legal_units = document.canonical_json["legal_units"]

    assert document.document_type == "law"
    assert document.language_code == "sr"
    assert document.title == "Zakon O Sumama"
    assert document.canonical_json["metadata"]["akoma_import"] is True
    assert [unit["unit_type"] for unit in legal_units] == ["article", "paragraph"]
    assert legal_units[0]["number"] == "1"
    assert legal_units[0]["heading"] == "Predmet"
    assert legal_units[1]["content_text"] == "Šume su dobro od opšteg interesa."


def test_canonical_service_exports_subitems_as_akoma_subpoints():
    article = ParsedLegalUnit(
        unit_type="article",
        number="1",
        ordinal=1,
        path="article:1",
        content_text="",
    )
    paragraph = ParsedLegalUnit(
        parent_legal_unit_id=article.legal_unit_id,
        unit_type="paragraph",
        number="1",
        ordinal=1,
        path="article:1/paragraph:1",
        content_text="",
    )
    item = ParsedLegalUnit(
        parent_legal_unit_id=paragraph.legal_unit_id,
        unit_type="item",
        number="1",
        ordinal=1,
        path="article:1/paragraph:1/item:1",
        content_text="",
    )
    subitem = ParsedLegalUnit(
        parent_legal_unit_id=item.legal_unit_id,
        unit_type="subitem",
        number="1",
        ordinal=1,
        path="article:1/paragraph:1/item:1/subitem:1",
        content_text="Prvi poduslov.",
    )
    parsed = ParsedLegalDocument(
        source_uri="file:///tmp/zakon.txt",
        filename="zakon.txt",
        document_type="law",
        title="Zakon o podtackama",
        legal_units=[article, paragraph, item, subitem],
    )
    service = CanonicalService()
    canonical = service.to_canonical_json(CanonicalizeRequest(document=parsed))

    response = service.export_akoma_ntoso(
        ExportAkomaNtosoRequest(document=canonical.document)
    )

    root = ET.fromstring(response.xml_text)
    namespace = {"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"}
    subpoint = root.find(".//akn:hcontainer[@name='subpoint']", namespace)
    assert subpoint is not None
    assert subpoint.attrib["eId"] == "article_1_paragraph_1_item_1_subitem_1"
    assert subpoint.find("akn:content/akn:p", namespace).text == "Prvi poduslov."


def test_canonical_service_exports_alineas_as_akoma_alineas():
    article = ParsedLegalUnit(
        unit_type="article",
        number="1",
        ordinal=1,
        path="article:1",
        content_text="",
    )
    paragraph = ParsedLegalUnit(
        parent_legal_unit_id=article.legal_unit_id,
        unit_type="paragraph",
        number="1",
        ordinal=1,
        path="article:1/paragraph:1",
        content_text="",
    )
    alinea = ParsedLegalUnit(
        parent_legal_unit_id=paragraph.legal_unit_id,
        unit_type="alinea",
        number="1",
        ordinal=1,
        path="article:1/paragraph:1/alinea:1",
        content_text="Prva mera.",
    )
    parsed = ParsedLegalDocument(
        source_uri="file:///tmp/zakon.txt",
        filename="zakon.txt",
        document_type="law",
        title="Zakon o alinejama",
        legal_units=[article, paragraph, alinea],
    )
    service = CanonicalService()
    canonical = service.to_canonical_json(CanonicalizeRequest(document=parsed))

    response = service.export_akoma_ntoso(
        ExportAkomaNtosoRequest(document=canonical.document)
    )

    root = ET.fromstring(response.xml_text)
    namespace = {"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"}
    alinea_node = root.find(".//akn:alinea", namespace)
    assert alinea_node is not None
    assert alinea_node.attrib["eId"] == "article_1_paragraph_1_alinea_1"
    assert alinea_node.find("akn:content/akn:p", namespace).text == "Prva mera."
