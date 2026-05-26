"""Canonical JSON conversion service."""

from functools import lru_cache
import re
import xml.etree.ElementTree as ET
from uuid import NAMESPACE_URL, uuid5

from zaikon.core.schemas import LanguageCode, ModuleHealth
from zaikon.modules.canonical.schemas import (
    CanonicalDocument,
    CanonicalizeRequest,
    CanonicalizeResponse,
    ExportAkomaNtosoRequest,
    ExportAkomaNtosoResponse,
    ImportAkomaNtosoRequest,
    ImportAkomaNtosoResponse,
)


class CanonicalService:
    """Converts parsed legal documents into the internal canonical JSON model."""

    schema_version = "0.1"
    akoma_namespace = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"

    def health(self) -> ModuleHealth:
        return ModuleHealth(module_name="canonical")

    def to_canonical_json(
        self, request: CanonicalizeRequest
    ) -> CanonicalizeResponse:
        parsed = request.document
        legal_units = [
            {
                "legal_unit_id": str(unit.legal_unit_id),
                "parent_legal_unit_id": (
                    str(unit.parent_legal_unit_id)
                    if unit.parent_legal_unit_id is not None
                    else None
                ),
                "unit_type": unit.unit_type,
                "number": unit.number,
                "ordinal": unit.ordinal,
                "heading": unit.heading,
                "content_text": unit.content_text,
                "path": unit.path,
                "metadata": unit.metadata,
            }
            for unit in parsed.legal_units
        ]
        canonical_json = {
            "schema_version": self.schema_version,
            "document": {
                "source_uri": parsed.source_uri,
                "filename": parsed.filename,
                "document_type": parsed.document_type,
                "title": parsed.title,
                "language_code": parsed.language_code.value,
            },
            "legal_units": legal_units,
            "metadata": {
                **parsed.metadata,
                "canonical_unit_count": len(legal_units),
            },
        }
        document = CanonicalDocument(
            source_uri=parsed.source_uri,
            filename=parsed.filename,
            document_type=parsed.document_type,
            title=parsed.title,
            language_code=parsed.language_code,
            canonical_json=canonical_json,
        )
        return CanonicalizeResponse(document=document)

    def import_akoma_ntoso(
        self, request: ImportAkomaNtosoRequest
    ) -> ImportAkomaNtosoResponse:
        root = ET.fromstring(request.xml_text)
        act = self._find_first(root, "act")
        document_type = act.get("name") if act is not None and act.get("name") else request.document_type
        language_code = self._language_from_akoma(root) or request.language_code
        legal_units = []

        body = self._find_first(root, "body")
        if body is not None:
            for article_ordinal, article in enumerate(
                self._children_named(body, "article"), start=1
            ):
                article_number = self._number_from_element(article) or str(article_ordinal)
                article_path = f"article:{article_number}"
                article_id = str(uuid5(NAMESPACE_URL, f"{request.source_uri}#{article_path}"))
                paragraphs = list(self._children_named(article, "paragraph"))
                legal_units.append(
                    {
                        "legal_unit_id": article_id,
                        "parent_legal_unit_id": None,
                        "unit_type": "article",
                        "number": article_number,
                        "ordinal": article_ordinal,
                        "heading": self._text_of_child(article, "heading"),
                        "content_text": self._content_text(article) if not paragraphs else "",
                        "path": article_path,
                        "metadata": {"akoma_eid": article.get("eId")},
                    }
                )
                for paragraph_ordinal, paragraph in enumerate(paragraphs, start=1):
                    paragraph_number = (
                        self._number_from_element(paragraph) or str(paragraph_ordinal)
                    )
                    paragraph_path = f"{article_path}/paragraph:{paragraph_number}"
                    paragraph_id = str(
                        uuid5(NAMESPACE_URL, f"{request.source_uri}#{paragraph_path}")
                    )
                    legal_units.append(
                        {
                            "legal_unit_id": paragraph_id,
                            "parent_legal_unit_id": article_id,
                            "unit_type": "paragraph",
                            "number": paragraph_number,
                            "ordinal": paragraph_ordinal,
                            "heading": None,
                            "content_text": self._content_text(paragraph),
                            "path": paragraph_path,
                            "metadata": {"akoma_eid": paragraph.get("eId")},
                        }
                    )
                    self._append_imported_child_units(
                        legal_units=legal_units,
                        source_uri=request.source_uri,
                        parent=paragraph,
                        parent_id=paragraph_id,
                        parent_path=paragraph_path,
                    )

        title = self._title_from_akoma(root) or request.filename
        canonical_json = {
            "schema_version": self.schema_version,
            "document": {
                "source_uri": request.source_uri,
                "filename": request.filename,
                "document_type": document_type,
                "title": title,
                "language_code": language_code.value,
            },
            "legal_units": legal_units,
            "metadata": {
                "canonical_unit_count": len(legal_units),
                "akoma_import": True,
            },
        }
        return ImportAkomaNtosoResponse(
            document=CanonicalDocument(
                source_uri=request.source_uri,
                filename=request.filename,
                document_type=document_type,
                title=title,
                language_code=language_code,
                canonical_json=canonical_json,
            )
        )

    def export_akoma_ntoso(
        self, request: ExportAkomaNtosoRequest
    ) -> ExportAkomaNtosoResponse:
        document = request.document
        ET.register_namespace("", self.akoma_namespace)
        akoma = ET.Element(self._akn_tag("akomaNtoso"))
        act = ET.SubElement(akoma, self._akn_tag("act"), {"name": document.document_type})
        self._append_meta(act, document)
        body = ET.SubElement(act, self._akn_tag("body"))

        legal_units = document.canonical_json.get("legal_units", [])
        children_by_parent: dict[str | None, list[dict]] = {}
        for unit in legal_units:
            parent_id = unit.get("parent_legal_unit_id")
            children_by_parent.setdefault(parent_id, []).append(unit)
        for children in children_by_parent.values():
            children.sort(key=lambda unit: unit.get("ordinal") or 0)

        for unit in children_by_parent.get(None, []):
            self._append_legal_unit(body, unit, children_by_parent)

        self._indent(akoma)
        xml_text = ET.tostring(akoma, encoding="unicode", short_empty_elements=False)
        return ExportAkomaNtosoResponse(xml_text=f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_text}')

    def _append_meta(self, act: ET.Element, document: CanonicalDocument) -> None:
        meta = ET.SubElement(act, self._akn_tag("meta"))
        identification = ET.SubElement(
            meta,
            self._akn_tag("identification"),
            {"source": "#zaikon"},
        )
        frbr_uri = self._frbr_uri(document)
        work = ET.SubElement(identification, self._akn_tag("FRBRWork"))
        ET.SubElement(work, self._akn_tag("FRBRthis"), {"value": frbr_uri})
        ET.SubElement(work, self._akn_tag("FRBRuri"), {"value": frbr_uri})
        ET.SubElement(work, self._akn_tag("FRBRcountry"), {"value": "rs"})
        ET.SubElement(work, self._akn_tag("FRBRauthor"), {"href": "#unknown"})
        expression = ET.SubElement(identification, self._akn_tag("FRBRExpression"))
        ET.SubElement(expression, self._akn_tag("FRBRthis"), {"value": f"{frbr_uri}/srp"})
        ET.SubElement(expression, self._akn_tag("FRBRuri"), {"value": f"{frbr_uri}/srp"})
        ET.SubElement(expression, self._akn_tag("FRBRlanguage"), {"language": "srp"})
        manifestation = ET.SubElement(
            identification, self._akn_tag("FRBRManifestation")
        )
        ET.SubElement(
            manifestation,
            self._akn_tag("FRBRthis"),
            {"value": f"{frbr_uri}/srp.xml"},
        )
        ET.SubElement(
            manifestation,
            self._akn_tag("FRBRuri"),
            {"value": f"{frbr_uri}/srp.xml"},
        )

    def _append_legal_unit(
        self,
        parent: ET.Element,
        unit: dict,
        children_by_parent: dict[str | None, list[dict]],
    ) -> None:
        unit_type = unit.get("unit_type")
        tag = self._akoma_tag_for_unit(unit_type)
        attributes = {"eId": self._eid(unit)}
        hcontainer_name = self._hcontainer_name_for_unit(unit_type)
        if hcontainer_name is not None:
            attributes["name"] = hcontainer_name
        element = ET.SubElement(parent, self._akn_tag(tag), attributes)

        number = unit.get("number")
        if number:
            ET.SubElement(element, self._akn_tag("num")).text = self._unit_num_text(
                unit_type, number
            )
        heading = unit.get("heading")
        if heading:
            ET.SubElement(element, self._akn_tag("heading")).text = heading

        children = children_by_parent.get(unit.get("legal_unit_id"), [])
        content_text = (unit.get("content_text") or "").strip()
        if content_text and not children:
            content = ET.SubElement(element, self._akn_tag("content"))
            ET.SubElement(content, self._akn_tag("p")).text = content_text

        for child in children:
            self._append_legal_unit(element, child, children_by_parent)

    def _akoma_tag_for_unit(self, unit_type: str | None) -> str:
        if unit_type == "article":
            return "article"
        if unit_type == "paragraph":
            return "paragraph"
        if unit_type == "alinea":
            return "alinea"
        return "hcontainer"

    def _hcontainer_name_for_unit(self, unit_type: str | None) -> str | None:
        if unit_type == "subitem":
            return "subpoint"
        if unit_type in {"section", "item"}:
            return unit_type
        return None

    def _unit_num_text(self, unit_type: str | None, number: str) -> str:
        if unit_type == "article":
            return f"Clan {number}."
        if unit_type == "paragraph":
            return f"({number})"
        return number

    def _frbr_uri(self, document: CanonicalDocument) -> str:
        slug = self._slug(document.title or document.filename or "document")
        return f"/akn/rs/act/{slug}"

    def _slug(self, value: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
        return normalized or "document"

    def _eid(self, unit: dict) -> str:
        path = unit.get("path") or unit.get("legal_unit_id") or "unit"
        return re.sub(r"[^A-Za-z0-9_]+", "_", path).strip("_") or "unit"

    def _akn_tag(self, name: str) -> str:
        return f"{{{self.akoma_namespace}}}{name}"

    def _local_name(self, element: ET.Element) -> str:
        return element.tag.rsplit("}", 1)[-1]

    def _find_first(self, root: ET.Element, name: str) -> ET.Element | None:
        for element in root.iter():
            if self._local_name(element) == name:
                return element
        return None

    def _children_named(self, element: ET.Element, name: str) -> list[ET.Element]:
        return [child for child in list(element) if self._local_name(child) == name]

    def _text_of_child(self, element: ET.Element, name: str) -> str | None:
        child = next(
            (item for item in list(element) if self._local_name(item) == name),
            None,
        )
        if child is None or child.text is None:
            return None
        value = child.text.strip()
        return value or None

    def _number_from_element(self, element: ET.Element) -> str | None:
        raw = self._text_of_child(element, "num")
        if raw is None:
            return None
        match = re.search(r"(\d+[a-z]?)", raw, re.IGNORECASE)
        return match.group(1) if match else raw.strip(" .()")

    def _content_text(self, element: ET.Element) -> str:
        content = next(
            (item for item in list(element) if self._local_name(item) == "content"),
            None,
        )
        if content is None:
            return ""
        paragraphs = [
            "".join(item.itertext()).strip()
            for item in content.iter()
            if self._local_name(item) == "p"
        ]
        return "\n".join(item for item in paragraphs if item)

    def _append_imported_child_units(
        self,
        *,
        legal_units: list[dict],
        source_uri: str,
        parent: ET.Element,
        parent_id: str,
        parent_path: str,
    ) -> None:
        child_ordinal = 0
        for child in list(parent):
            unit_type = self._unit_type_from_akoma_element(child)
            if unit_type is None:
                continue
            child_ordinal += 1
            number = self._number_from_element(child) or str(child_ordinal)
            child_path = f"{parent_path}/{unit_type}:{number}"
            child_id = str(uuid5(NAMESPACE_URL, f"{source_uri}#{child_path}"))
            legal_units.append(
                {
                    "legal_unit_id": child_id,
                    "parent_legal_unit_id": parent_id,
                    "unit_type": unit_type,
                    "number": number,
                    "ordinal": child_ordinal,
                    "heading": self._text_of_child(child, "heading"),
                    "content_text": self._content_text(child),
                    "path": child_path,
                    "metadata": {"akoma_eid": child.get("eId")},
                }
            )
            self._append_imported_child_units(
                legal_units=legal_units,
                source_uri=source_uri,
                parent=child,
                parent_id=child_id,
                parent_path=child_path,
            )

    def _unit_type_from_akoma_element(self, element: ET.Element) -> str | None:
        local_name = self._local_name(element)
        if local_name == "alinea":
            return "alinea"
        if local_name != "hcontainer":
            return None
        name = element.get("name")
        if name == "item":
            return "item"
        if name == "subpoint":
            return "subitem"
        return None

    def _language_from_akoma(self, root: ET.Element) -> LanguageCode | None:
        language = self._find_first(root, "FRBRlanguage")
        value = language.get("language") if language is not None else None
        if value in {"sr", "srp"}:
            return LanguageCode.sr
        if value in {"mk", "mkd"}:
            return LanguageCode.mk
        return None

    def _title_from_akoma(self, root: ET.Element) -> str | None:
        frbr_uri = self._find_first(root, "FRBRuri")
        value = frbr_uri.get("value") if frbr_uri is not None else None
        if not value:
            return None
        return value.rstrip("/").split("/")[-1].replace("-", " ").title()

    def _indent(self, element: ET.Element, level: int = 0) -> None:
        indentation = "\n" + level * "  "
        if len(element):
            if not element.text or not element.text.strip():
                element.text = indentation + "  "
            for child in element:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indentation
        if level and (not element.tail or not element.tail.strip()):
            element.tail = indentation


@lru_cache
def get_canonical_service() -> CanonicalService:
    return CanonicalService()
