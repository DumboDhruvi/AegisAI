"""Main FastAPI application entry point for AegisAI."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aegis.api.routes.agent import router as agent_router
from aegis.api.routes.benchmark import router as benchmark_router
from aegis.api.routes.cicd import router as cicd_router
from aegis.api.routes.data_validation import router as validation_router
from aegis.api.routes.datasets import router as datasets_router
from aegis.api.routes.evaluation import router as evaluation_router
from aegis.api.routes.grounding import router as grounding_router
from aegis.api.routes.rag import router as rag_router
from aegis.api.routes.regression import router as regression_router
from aegis.api.routes.robustness import router as robustness_router
from aegis.api.routes.rubrics import router as rubrics_router
from aegis.core.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title="AegisAI Platform API",
        description="Enterprise AI Reliability, Evaluation, and Benchmarking Platform",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Cross-Origin Resource Sharing
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health Check
    @app.get("/health", tags=["Health"])
    def health_check() -> dict[str, Any]:
        return {
            "status": "healthy",
            "environment": settings.environment,
            "version": "0.1.0",
        }

    # Include Routers
    app.include_router(datasets_router, prefix="/api/v1")
    app.include_router(rag_router, prefix="/api/v1")
    app.include_router(evaluation_router, prefix="/api/v1")
    app.include_router(rubrics_router, prefix="/api/v1")
    app.include_router(grounding_router, prefix="/api/v1")
    app.include_router(robustness_router, prefix="/api/v1")
    app.include_router(agent_router, prefix="/api/v1")
    app.include_router(benchmark_router, prefix="/api/v1")
    app.include_router(regression_router, prefix="/api/v1")
    app.include_router(validation_router, prefix="/api/v1")
    app.include_router(cicd_router, prefix="/api/v1")

    return app


app = create_app()
