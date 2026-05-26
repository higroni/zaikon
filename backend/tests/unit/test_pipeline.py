"""Unit tests for the scaffold pipeline framework."""

from zaikon.pipeline.chains import PipelineChain
from zaikon.pipeline.steps.dummy import EchoStep
from zaikon.core.schemas import JobStatus


def test_echo_chain_completes_and_writes_artifact():
    chain = PipelineChain(chain_name="EchoChain", steps=[EchoStep()])
    context = chain.run({"message": "hello"})

    assert context.status == JobStatus.completed
    assert context.get_artifact("echo_result") is not None
    assert context.get_artifact("echo_result").payload == {"message": "hello"}

