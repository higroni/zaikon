"""FastAPI entry point for zAIkon."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from zaikon.api.routers.corpus import import_jobs_router, router as corpus_router
from zaikon.api.routers.documents import router as documents_router
from zaikon.api.routers.draft_reviews import router as draft_reviews_router
from zaikon.api.routers.health import router as health_router
from zaikon.api.routers.pipeline import router as pipeline_router
from zaikon.api.routers.search import router as search_router
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
    app.include_router(corpus_router, prefix="/api/v1")
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(draft_reviews_router, prefix="/api/v1")
    app.include_router(import_jobs_router, prefix="/api/v1")
    app.include_router(pipeline_router, prefix="/api/v1")
    app.include_router(search_router, prefix="/api/v1")
    return app


app = create_app()

