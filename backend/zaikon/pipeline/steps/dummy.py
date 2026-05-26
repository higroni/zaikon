"""Dummy pipeline step used by scaffold and tests."""

from zaikon.pipeline.base import PipelineStep
from zaikon.pipeline.context import PipelineContext


class EchoStep(PipelineStep):
    step_name = "echo"
    produces = ("echo_result",)

    def run(self, context: PipelineContext) -> PipelineContext:
        message = context.inputs.get("message", "zAIkon pipeline ready")
        context.add_artifact(
            self.artifact(
                name="echo_result",
                artifact_type="application/json",
                payload={"message": message},
            )
        )
        return context

