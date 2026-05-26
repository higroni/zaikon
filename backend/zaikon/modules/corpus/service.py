"""Corpus module service implementation."""

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from uuid import UUID

from zaikon.core.config import settings
from zaikon.core.schemas import JobStatus, ModuleHealth
from zaikon.modules.corpus.artifact_store import CorpusArtifactStore
from zaikon.modules.corpus.schemas import (
    CorpusRecord,
    CreateCorpusRequest,
    CreateCorpusResponse,
    ImportFolderRequest,
    ImportFolderResponse,
    ImportJobRecord,
    ImportReport,
    ImportReportResponse,
    SourceFileRecord,
)
from zaikon.pipeline.steps.corpus.folder_import import CorpusFolderImportChain


class CorpusService:
    """In-process Corpus service following the public module contract."""

    def __init__(self, artifact_dir: Path | None = None) -> None:
        self._store = CorpusArtifactStore(artifact_dir or settings.artifact_dir)
        self._corpora: dict[UUID, CorpusRecord] = self._store.load_corpora()
        self._import_jobs: dict[UUID, ImportJobRecord] = (
            self._store.load_import_jobs()
        )
        self._import_reports: dict[UUID, ImportReport] = (
            self._store.load_import_reports()
        )

    def health(self) -> ModuleHealth:
        return ModuleHealth(module_name="corpus")

    def create_corpus(self, request: CreateCorpusRequest) -> CreateCorpusResponse:
        corpus = CorpusRecord(**request.model_dump())
        self._corpora[corpus.corpus_id] = corpus
        self._store.save_corpora(list(self._corpora.values()))
        return CreateCorpusResponse(corpus=corpus)

    def list_corpora(self) -> list[CorpusRecord]:
        return list(self._corpora.values())

    def get_corpus(self, corpus_id: UUID) -> CorpusRecord | None:
        return self._corpora.get(corpus_id)

    def import_folder(self, request: ImportFolderRequest) -> ImportFolderResponse:
        if request.corpus_id not in self._corpora:
            raise KeyError(f"Corpus not found: {request.corpus_id}")

        chain = CorpusFolderImportChain()
        context = chain.run(
            {
                "corpus_id": str(request.corpus_id),
                "folder_uri": request.folder_uri,
                "recursive": request.recursive,
            }
        )

        report_payload = context.get_artifact("import_report")
        if report_payload is None:
            raise RuntimeError("Corpus import did not produce import_report")

        source_files = [
            SourceFileRecord(corpus_id=request.corpus_id, **item)
            for item in report_payload.payload["source_files"]
        ]
        summary = report_payload.payload["summary"]
        import_job = ImportJobRecord(
            import_job_id=context.pipeline_run_id,
            corpus_id=request.corpus_id,
            folder_uri=request.folder_uri,
            status=JobStatus.completed,
            total_files=summary["total_files"],
            supported_files=summary["supported_files"],
            unsupported_files=summary["unsupported_files"],
            completed_at=datetime.utcnow(),
        )
        report = ImportReport(
            import_job_id=import_job.import_job_id,
            corpus_id=request.corpus_id,
            status=import_job.status,
            source_files=source_files,
            warnings=report_payload.payload["warnings"],
            summary=summary,
            index_reports=report_payload.payload.get("index_reports", {}),
            storage_report=report_payload.payload.get("storage_report"),
            pipeline_run_id=report_payload.payload.get("pipeline_run_id"),
            artifact_names=sorted(context.artifacts),
        )
        self._import_jobs[import_job.import_job_id] = import_job
        self._import_reports[import_job.import_job_id] = report
        self._store.save_import_jobs(list(self._import_jobs.values()))
        self._store.save_import_report(report)
        self._store.save_pipeline_artifacts(import_job.import_job_id, context.artifacts)
        return ImportFolderResponse(import_job=import_job, report=report)

    def list_import_jobs(self, corpus_id: UUID) -> list[ImportJobRecord]:
        return [
            job for job in self._import_jobs.values() if job.corpus_id == corpus_id
        ]

    def get_import_job(self, import_job_id: UUID) -> ImportJobRecord | None:
        return self._import_jobs.get(import_job_id)

    def get_import_report(self, import_job_id: UUID) -> ImportReportResponse:
        report = self._import_reports.get(import_job_id)
        if report is None:
            raise KeyError(f"Import job report not found: {import_job_id}")
        return ImportReportResponse(report=report)

    def list_import_artifacts(self, import_job_id: UUID) -> list[str]:
        if import_job_id not in self._import_jobs:
            raise KeyError(f"Import job not found: {import_job_id}")
        return self._store.list_pipeline_artifact_names(import_job_id)

    def get_import_artifact(self, import_job_id: UUID, artifact_name: str):
        if import_job_id not in self._import_jobs:
            raise KeyError(f"Import job not found: {import_job_id}")
        artifact = self._store.load_pipeline_artifact(import_job_id, artifact_name)
        if artifact is None:
            raise KeyError(f"Import artifact not found: {artifact_name}")
        return artifact


@lru_cache
def get_corpus_service() -> CorpusService:
    return CorpusService()
