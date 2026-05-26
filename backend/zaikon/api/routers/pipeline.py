"""Pipeline endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from zaikon.pipeline.chains import PipelineChain
from zaikon.pipeline.context import PipelineContext
from zaikon.pipeline.steps.dummy import EchoStep

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class EchoPipelineRequest(BaseModel):
    message: str = "zAIkon pipeline ready"


@router.post("/echo", response_model=PipelineContext)
def run_echo_pipeline(request: EchoPipelineRequest) -> PipelineContext:
    chain = PipelineChain(chain_name="EchoChain", steps=[EchoStep()])
    return chain.run(inputs=request.model_dump())

