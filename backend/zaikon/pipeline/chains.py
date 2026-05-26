"""Pipeline chain runner."""

from collections.abc import Iterable

from zaikon.core.schemas import JobStatus
from zaikon.pipeline.base import PipelineStep
from zaikon.pipeline.context import PipelineContext


class PipelineChain:
    """Runs a sequence of pipeline steps."""

    def __init__(self, chain_name: str, steps: Iterable[PipelineStep]):
        self.chain_name = chain_name
        self.steps = list(steps)

    def run(self, inputs: dict | None = None) -> PipelineContext:
        context = PipelineContext(chain_name=self.chain_name, inputs=inputs or {})
        context.status = JobStatus.running
        context.log("INFO", f"Started chain {self.chain_name}")

        try:
            for step in self.steps:
                context.log("INFO", f"Running step {step.step_name}", step.step_name)
                step.validate_requirements(context)
                context = step.run(context)
                context.log("INFO", f"Completed step {step.step_name}", step.step_name)
            context.status = JobStatus.completed
            context.log("INFO", f"Completed chain {self.chain_name}")
            return context
        except Exception as exc:
            context.status = JobStatus.failed
            context.log("ERROR", str(exc))
            raise
        finally:
            context.touch()

