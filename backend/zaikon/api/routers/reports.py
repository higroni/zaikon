"""Report endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from zaikon.modules.reports.schemas import (
    GenerateReportRequest,
    GenerateReportResponse,
    ReportRecord,
)
from zaikon.modules.reports.service import get_report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=GenerateReportResponse)
def generate_report(request: GenerateReportRequest) -> GenerateReportResponse:
    try:
        return get_report_service().generate_report(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[ReportRecord])
def list_reports() -> list[ReportRecord]:
    return get_report_service().list_reports()


@router.get("/{report_id}", response_model=ReportRecord)
def get_report(report_id: UUID) -> ReportRecord:
    report = get_report_service().get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/download")
def download_report(report_id: UUID) -> Response:
    download = get_report_service().get_download(report_id)
    if download is None:
        raise HTTPException(status_code=404, detail="Report not found")
    content, media_type, filename = download
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
