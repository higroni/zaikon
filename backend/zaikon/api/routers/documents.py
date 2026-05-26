"""Document catalog endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from zaikon.modules.canonical.schemas import CanonicalDocument, ExportAkomaNtosoRequest
from zaikon.modules.canonical.service import get_canonical_service
from zaikon.modules.documents.catalog import (
    DocumentCatalogService,
    DocumentDetail,
    DocumentSummary,
    LegalUnitRecord,
)

router = APIRouter(tags=["documents"])


@router.get("/documents", response_model=list[DocumentSummary])
def list_documents(corpus_id: UUID | None = None) -> list[DocumentSummary]:
    return DocumentCatalogService().list_documents(corpus_id=corpus_id)


@router.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document(document_id: UUID) -> DocumentDetail:
    document = DocumentCatalogService().get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/documents/{document_id}/akoma-ntoso")
def export_document_akoma_ntoso(document_id: UUID) -> Response:
    document = DocumentCatalogService().get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    canonical = CanonicalDocument(
        source_uri=document.source_uri,
        filename=document.filename,
        document_type=document.document_type,
        title=document.title,
        canonical_json=document.canonical_json,
    )
    response = get_canonical_service().export_akoma_ntoso(
        ExportAkomaNtosoRequest(document=canonical)
    )
    return Response(content=response.xml_text, media_type="application/xml")


@router.get("/legal-units/{legal_unit_id}", response_model=LegalUnitRecord)
def get_legal_unit(legal_unit_id: str) -> LegalUnitRecord:
    legal_unit = DocumentCatalogService().get_legal_unit(legal_unit_id)
    if legal_unit is None:
        raise HTTPException(status_code=404, detail="Legal unit not found")
    return legal_unit
