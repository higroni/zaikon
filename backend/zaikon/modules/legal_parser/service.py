"""Serbian legal structure parser implementation."""

from functools import lru_cache
import re

from zaikon.core.schemas import ModuleHealth
from zaikon.modules.legal_parser.schemas import (
    ParsedLegalDocument,
    ParsedLegalUnit,
    ParseLegalStructureRequest,
    ParseLegalStructureResponse,
)


_FOLD_TRANSLATION = str.maketrans(
    {
        "č": "c",
        "ć": "c",
        "š": "s",
        "đ": "dj",
        "ž": "z",
        "Č": "C",
        "Ć": "C",
        "Š": "S",
        "Đ": "Dj",
        "Ž": "Z",
    }
)
_ARTICLE_RE = re.compile(r"^clan\s+(\d+[a-z]?)\.?$", re.IGNORECASE)
_ROMAN_SECTION_RE = re.compile(
    r"^([IVXLCDM]+)\.\s+(.+)$",
    re.IGNORECASE,
)
_NUMBERED_ITEM_RE = re.compile(r"^(\d+)\.\s+(.+)$")
_INLINE_ITEM_RE = re.compile(
    r"(?:^|\s)(\d+)\)\s+(.+?)(?=\s+\d+\)\s+|$)",
    re.DOTALL,
)


def _fold_serbian_latin(value: str) -> str:
    return value.translate(_FOLD_TRANSLATION)


def _split_blocks(lines: list[str]) -> list[str]:
    blocks = []
    current = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                blocks.append(" ".join(current).strip())
                current = []
            continue
        current.append(stripped)
    if current:
        blocks.append(" ".join(current).strip())
    return blocks


class LegalParserService:
    """Rule-based parser for normalized Serbian legal text."""

    def health(self) -> ModuleHealth:
        return ModuleHealth(module_name="legal_parser")

    def parse_legal_structure(
        self, request: ParseLegalStructureRequest
    ) -> ParseLegalStructureResponse:
        lines = request.content_text.splitlines()
        article_markers = self._find_article_markers(lines)
        legal_units: list[ParsedLegalUnit] = []
        title = self._title_before_first_article(lines, article_markers)
        section_markers = self._find_section_markers(lines)

        for section_ordinal, (line_index, number, heading) in enumerate(
            section_markers, start=1
        ):
            legal_units.append(
                ParsedLegalUnit(
                    unit_type="section",
                    number=number,
                    ordinal=section_ordinal,
                    heading=heading,
                    content_text="",
                    path=f"section:{number}",
                    metadata={"line_index": line_index},
                )
            )

        for article_ordinal, (line_index, number) in enumerate(article_markers, start=1):
            next_index = (
                article_markers[article_ordinal][0]
                if article_ordinal < len(article_markers)
                else len(lines)
            )
            article_lines = lines[line_index + 1 : next_index]
            heading = self._heading_before_marker(lines, line_index)
            article_content = "\n".join(line.strip() for line in article_lines).strip()
            article_unit = ParsedLegalUnit(
                unit_type="article",
                number=number,
                ordinal=article_ordinal,
                heading=heading,
                content_text=article_content,
                path=f"article:{number}",
            )
            legal_units.append(article_unit)

            paragraph_blocks = _split_blocks(article_lines)
            for paragraph_ordinal, paragraph_text in enumerate(
                paragraph_blocks, start=1
            ):
                paragraph_unit = ParsedLegalUnit(
                    parent_legal_unit_id=article_unit.legal_unit_id,
                    unit_type="paragraph",
                    number=str(paragraph_ordinal),
                    ordinal=paragraph_ordinal,
                    heading=None,
                    content_text=paragraph_text,
                    path=f"article:{number}/paragraph:{paragraph_ordinal}",
                )
                legal_units.append(paragraph_unit)
                legal_units.extend(
                    self._parse_inline_items(
                        paragraph_text=paragraph_text,
                        paragraph_unit=paragraph_unit,
                    )
                )

        if not article_markers:
            legal_units.extend(self._parse_numbered_items(lines))

        document = ParsedLegalDocument(
            source_uri=request.source_uri,
            filename=request.filename,
            document_type=request.document_type,
            title=title,
            language_code=request.language_code,
            legal_units=legal_units,
            metadata={
                "section_count": sum(
                    1 for unit in legal_units if unit.unit_type == "section"
                ),
                "article_count": sum(
                    1 for unit in legal_units if unit.unit_type == "article"
                ),
                "paragraph_count": sum(
                    1 for unit in legal_units if unit.unit_type == "paragraph"
                ),
                "item_count": sum(
                    1 for unit in legal_units if unit.unit_type == "item"
                ),
            },
        )
        return ParseLegalStructureResponse(document=document)

    def _find_article_markers(self, lines: list[str]) -> list[tuple[int, str]]:
        markers = []
        for index, line in enumerate(lines):
            folded = _fold_serbian_latin(line.strip())
            match = _ARTICLE_RE.match(folded)
            if match:
                markers.append((index, match.group(1)))
        return markers

    def _find_section_markers(self, lines: list[str]) -> list[tuple[int, str, str]]:
        markers = []
        for index, line in enumerate(lines):
            stripped = line.strip()
            match = _ROMAN_SECTION_RE.match(stripped)
            if match:
                markers.append((index, match.group(1), match.group(2).strip()))
        return markers

    def _heading_before_marker(self, lines: list[str], marker_index: int) -> str | None:
        for index in range(marker_index - 1, -1, -1):
            candidate = lines[index].strip()
            if not candidate:
                continue
            if _ROMAN_SECTION_RE.match(candidate):
                return None
            folded = _fold_serbian_latin(candidate)
            if _ARTICLE_RE.match(folded):
                return None
            return candidate
        return None

    def _parse_numbered_items(self, lines: list[str]) -> list[ParsedLegalUnit]:
        units = []
        item_markers = []
        for index, line in enumerate(lines):
            match = _NUMBERED_ITEM_RE.match(line.strip())
            if match:
                item_markers.append((index, match.group(1), match.group(2).strip()))

        for item_ordinal, (line_index, number, first_text) in enumerate(
            item_markers, start=1
        ):
            next_index = (
                item_markers[item_ordinal][0]
                if item_ordinal < len(item_markers)
                else len(lines)
            )
            continuation = [
                line.strip()
                for line in lines[line_index + 1 : next_index]
                if line.strip()
            ]
            content_parts = [first_text, *continuation]
            units.append(
                ParsedLegalUnit(
                    unit_type="item",
                    number=number,
                    ordinal=item_ordinal,
                    heading=None,
                    content_text=" ".join(content_parts).strip(),
                    path=f"item:{number}",
                )
            )
        return units

    def _parse_inline_items(
        self,
        paragraph_text: str,
        paragraph_unit: ParsedLegalUnit,
    ) -> list[ParsedLegalUnit]:
        items = []
        for item_ordinal, match in enumerate(
            _INLINE_ITEM_RE.finditer(paragraph_text), start=1
        ):
            number = match.group(1)
            content_text = match.group(2).strip()
            items.append(
                ParsedLegalUnit(
                    parent_legal_unit_id=paragraph_unit.legal_unit_id,
                    unit_type="item",
                    number=number,
                    ordinal=item_ordinal,
                    heading=None,
                    content_text=content_text,
                    path=f"{paragraph_unit.path}/item:{number}",
                )
            )
        return items

    def _title_before_first_article(
        self, lines: list[str], article_markers: list[tuple[int, str]]
    ) -> str | None:
        end = article_markers[0][0] if article_markers else len(lines)
        blocks = _split_blocks(lines[:end])
        return blocks[0] if blocks else None


@lru_cache
def get_legal_parser_service() -> LegalParserService:
    return LegalParserService()
