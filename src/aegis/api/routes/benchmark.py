"""FastAPI routes for Multi-Model Comparative Benchmarking (Module 8)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from aegis.domain.models.benchmark import (
    BenchmarkComparisonReport,
    ModelPricing,
)
from aegis.domain.models.evaluation_case import EvaluationCase
from aegis.services.benchmarking_service import BenchmarkingService

router = APIRouter(prefix="/benchmark", tags=["Benchmarking"])

_service = BenchmarkingService()


class RunBenchmarkRequest(BaseModel):
    """Request payload to execute a comparative benchmark across models."""

    model_config = ConfigDict(extra="forbid")

    dataset_name: str = Field(..., min_length=1, description="Dataset label or name")
    cases: list[EvaluationCase] = Field(
        ..., min_length=1, description="List of evaluation cases to test"
    )
    model_ids: list[str] | None = Field(
        default=None, description="Specific models to benchmark (defaults to standard mock models)"
    )
    precomputed_answers: dict[str, dict[str, str]] | None = Field(
        default=None,
        description="Optional mapping of model_id -> case_id -> answer",
    )


@router.get(
    "/models",
    response_model=dict[str, ModelPricing],
    status_code=status.HTTP_200_OK,
    summary="List benchmark model pricing",
    description="Returns token pricing profiles and registered models available for benchmarking.",
)
async def list_models() -> dict[str, ModelPricing]:
    """Retrieve catalog of benchmark models and pricing."""
    return _service.get_pricing_catalog()


@router.post(
    "/run",
    response_model=BenchmarkComparisonReport,
    status_code=status.HTTP_200_OK,
    summary="Execute comparative benchmark",
    description=(
        "Evaluates identical test cases across multiple models, tracking accuracy, "
        "faithfulness, relevance, hallucination, latency, token usage, and cost."
    ),
)
async def run_benchmark(payload: RunBenchmarkRequest) -> BenchmarkComparisonReport:
    """Run comparative multi-model benchmark."""
    try:
        precomputed = payload.precomputed_answers
        if precomputed is None and payload.model_ids is not None:
            # Initialize empty map for specified model IDs
            precomputed = {m: {} for m in payload.model_ids}

        return await _service.run_benchmark(
            dataset_name=payload.dataset_name,
            cases=payload.cases,
            precomputed_answers=precomputed,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Benchmarking execution failed: {e}",
        ) from e
