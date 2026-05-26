"""Filesystem-backed artifact persistence for the corpus module."""

import json
from pathlib import Path
from uuid import UUID

from zaikon.modules.corpus.schemas import CorpusRecord, ImportJobRecord, ImportReport


class CorpusArtifactStore:
    """Stores corpus records, import jobs, reports, and pipeline artifacts as JSON."""

    def __init__(self, artifact_dir: Path) -> None:
        self.root = Path(artifact_dir)
        self.corpus_dir = self.root / "corpus"
        self.report_dir = self.corpus_dir / "import_reports"
        self.pipeline_artifact_dir = self.corpus_dir / "pipeline_artifacts"
        self.corpus_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.pipeline_artifact_dir.mkdir(parents=True, exist_ok=True)

    @property
    def corpora_path(self) -> Path:
        return self.corpus_dir / "corpora.json"

    @property
    def import_jobs_path(self) -> Path:
        return self.corpus_dir / "import_jobs.json"

    def load_corpora(self) -> dict[UUID, CorpusRecord]:
        payload = self._read_json_list(self.corpora_path)
        records = [CorpusRecord.model_validate(item) for item in payload]
        return {record.corpus_id: record for record in records}

    def save_corpora(self, corpora: list[CorpusRecord]) -> None:
        self._write_json(
            self.corpora_path,
            [record.model_dump(mode="json") for record in corpora],
        )

    def load_import_jobs(self) -> dict[UUID, ImportJobRecord]:
        payload = self._read_json_list(self.import_jobs_path)
        records = [ImportJobRecord.model_validate(item) for item in payload]
        return {record.import_job_id: record for record in records}

    def save_import_jobs(self, import_jobs: list[ImportJobRecord]) -> None:
        self._write_json(
            self.import_jobs_path,
            [record.model_dump(mode="json") for record in import_jobs],
        )

    def load_import_reports(self) -> dict[UUID, ImportReport]:
        reports = {}
        for path in self.report_dir.glob("*.json"):
            report = ImportReport.model_validate(self._read_json(path, {}))
            reports[report.import_job_id] = report
        return reports

    def save_import_report(self, report: ImportReport) -> None:
        self._write_json(
            self.report_dir / f"{report.import_job_id}.json",
            report.model_dump(mode="json"),
        )

    def save_pipeline_artifacts(self, import_job_id: UUID, artifacts: dict) -> None:
        artifact_dir = self.pipeline_artifact_dir / str(import_job_id)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        for name, artifact in artifacts.items():
            self._write_json(
                artifact_dir / f"{name}.json",
                artifact.model_dump(mode="json"),
            )

    def list_pipeline_artifact_names(self, import_job_id: UUID) -> list[str]:
        artifact_dir = self.pipeline_artifact_dir / str(import_job_id)
        if not artifact_dir.exists():
            return []
        return sorted(path.stem for path in artifact_dir.glob("*.json"))

    def load_pipeline_artifact(self, import_job_id: UUID, artifact_name: str):
        artifact_path = (
            self.pipeline_artifact_dir / str(import_job_id) / f"{artifact_name}.json"
        )
        if not artifact_path.exists():
            return None
        return self._read_json(artifact_path, None)

    def _read_json_list(self, path: Path) -> list:
        return self._read_json(path, [])

    def _read_json(self, path: Path, default):
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
