"""FastAPI entry point for zAIkon."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from zaikon.api.routers.health import router as health_router
from zaikon.api.routers.pipeline import router as pipeline_router
from zaikon.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="zAIkon API",
        description="AI-assisted legislative compliance review platform",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(pipeline_router, prefix="/api/v1")
    return app


app = create_app()

