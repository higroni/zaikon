"""Base pipeline step contract."""

from abc import ABC, abstractmethod

from zaikon.core.schemas import PipelineArtifact
from zaikon.pipeline.context import PipelineContext


class PipelineStep(ABC):
    """Base class for domain pipeline steps.

    Steps must be small, testable, and have a stable `step_name` listed in
    docs/master/MASTER_PIPELINE_STEPS.md.
    """

    step_name: str
    produces: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()

    def validate_requirements(self, context: PipelineContext) -> None:
        missing = [name for name in self.requires if context.get_artifact(name) is None]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Step '{self.step_name}' missing artifacts: {joined}")

    def artifact(self, name: str, artifact_type: str, payload) -> PipelineArtifact:
        return PipelineArtifact(name=name, artifact_type=artifact_type, payload=payload)

    @abstractmethod
    def run(self, context: PipelineContext) -> PipelineContext:
        """Execute the step and return the mutated context."""

