"""Report generation service."""

from functools import lru_cache
import json
from pathlib import Path
from uuid import UUID

from zaikon.core.config import settings
from zaikon.modules.draft_reviews.service import get_draft_review_service
from zaikon.modules.reports.schemas import (
    GenerateReportRequest,
    GenerateReportResponse,
    ReportRecord,
)


class ReportService:
    """Generates and stores review report artifacts."""

    def __init__(self, artifact_dir: Path | None = None) -> None:
        self.root = Path(artifact_dir or settings.artifact_dir) / "reports"
        self.root.mkdir(parents=True, exist_ok=True)

    def generate_report(self, request: GenerateReportRequest) -> GenerateReportResponse:
        if request.report_format != "markdown":
            raise ValueError("Only markdown reports are supported in the MVP")
        detail = get_draft_review_service().get_draft_review(request.pipeline_run_id)
        if detail is None:
            raise KeyError(f"Draft review not found: {request.pipeline_run_id}")

        content_text = self._render_markdown(detail)
        report = ReportRecord(
            pipeline_run_id=request.pipeline_run_id,
            report_format=request.report_format,
            title=f"Izvestaj - {detail.draft_review.title}",
            finding_count=len(detail.findings),
            content_text=content_text,
            metadata={
                "draft_review_status": detail.draft_review.status.value,
                "document_type": detail.draft_review.metadata.get("document_type"),
            },
        )
        self._save_report(report)
        return GenerateReportResponse(report=report)

    def get_report(self, report_id: UUID) -> ReportRecord | None:
        path = self.root / f"{report_id}.json"
        if not path.exists():
            return None
        return ReportRecord.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def list_reports(self) -> list[ReportRecord]:
        reports = [
            ReportRecord.model_validate(json.loads(path.read_text(encoding="utf-8")))
            for path in self.root.glob("*.json")
        ]
        return sorted(
            reports,
            key=lambda report: report.created_at.isoformat(),
            reverse=True,
        )

    def _save_report(self, report: ReportRecord) -> None:
        path = self.root / f"{report.report_id}.json"
        path.write_text(
            json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _render_markdown(self, detail) -> str:
        lines = [
            f"# Izvestaj - {detail.draft_review.title}",
            "",
            f"- Pipeline run: `{detail.draft_review.pipeline_run_id}`",
            f"- Status provere: `{detail.draft_review.status.value}`",
            f"- Broj nalaza: {len(detail.findings)}",
            "",
            "## Nalazi",
            "",
        ]
        if not detail.findings:
            lines.append("Nema nalaza.")
            return "\n".join(lines).strip() + "\n"

        for index, finding in enumerate(detail.findings, start=1):
            lines.extend(
                [
                    f"### {index}. {finding.title}",
                    "",
                    f"- Tip: `{finding.finding_type}`",
                    f"- Rizik: `{finding.risk_level.value}`",
                    f"- Status: `{finding.status.value}`",
                    f"- Putanja: `{finding.source_path or 'n/a'}`",
                    "",
                    finding.explanation,
                    "",
                ]
            )
            if finding.recommendation:
                lines.extend(["Preporuka:", "", finding.recommendation, ""])
            if finding.review_note:
                lines.extend(["Beleška pregleda:", "", finding.review_note, ""])
        return "\n".join(lines).strip() + "\n"


@lru_cache
def get_report_service() -> ReportService:
    return ReportService()
