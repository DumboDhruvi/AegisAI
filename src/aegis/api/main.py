"""Main FastAPI application entry point for AegisAI."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aegis.api.routes.datasets import router as datasets_router
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

    return app


app = create_app()
