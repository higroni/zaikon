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


@router.get("/{report_id}", response_model=ReportRecord)
def get_report(report_id: UUID) -> ReportRecord:
    report = get_report_service().get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/download")
def download_report(report_id: UUID) -> Response:
    report = get_report_service().get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    filename = f"{report.report_id}.md"
    return Response(
        content=report.content_text,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

