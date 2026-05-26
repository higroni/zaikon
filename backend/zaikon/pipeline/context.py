"""Pipeline context passed through all steps."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from zaikon.core.schemas import JobStatus, PipelineArtifact, PipelineLogEntry
from zaikon.core.time import utc_now


class PipelineContext(BaseModel):
    pipeline_run_id: UUID = Field(default_factory=uuid4)
    chain_name: str
    status: JobStatus = JobStatus.pending
    inputs: dict[str, Any] = Field(default_factory=dict)
    artifacts: dict[str, PipelineArtifact] = Field(default_factory=dict)
    logs: list[PipelineLogEntry] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def add_artifact(self, artifact: PipelineArtifact) -> None:
        self.artifacts[artifact.name] = artifact
        self.touch()

    def get_artifact(self, name: str) -> PipelineArtifact | None:
        return self.artifacts.get(name)

    def log(self, level: str, message: str, step_name: str | None = None) -> None:
        self.logs.append(
            PipelineLogEntry(level=level, message=message, step_name=step_name)
        )
        self.touch()

    def touch(self) -> None:
        self.updated_at = utc_now()

