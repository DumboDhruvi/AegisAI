"""FastAPI routes for Observability, Tracing, and Diagnostic Replay (Module 12)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from aegis.domain.models.observability import (
    EvaluationTraceRecord,
    TraceFilter,
    TraceSummary,
)
from aegis.services.observability_tracer import ObservabilityTracer

router = APIRouter(prefix="/observability", tags=["Observability & Tracing"])

_tracer = ObservabilityTracer()


@router.post(
    "/trace",
    response_model=dict[str, str],
    status_code=status.HTTP_201_CREATED,
    summary="Record execution trace",
    description=(
        "Captures request, prompt, model, retrieved context, latency, tokens, cost, and evaluation."
    ),
)
async def record_trace(trace: EvaluationTraceRecord) -> dict[str, str]:
    """Record an evaluation trace."""
    try:
        _tracer.record_trace(trace)
        return {"status": "recorded", "run_id": trace.run_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record trace: {e}",
        ) from e


@router.get(
    "/trace/{run_id}",
    response_model=EvaluationTraceRecord,
    status_code=status.HTTP_200_OK,
    summary="Get trace by run ID",
    description="Retrieves a complete evaluation execution trace by run ID.",
)
async def get_trace(run_id: str) -> EvaluationTraceRecord:
    """Retrieve an evaluation trace."""
    trace = _tracer.get_trace(run_id)
    if trace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace with run_id '{run_id}' not found.",
        )
    return trace


@router.get(
    "/traces",
    response_model=list[EvaluationTraceRecord],
    status_code=status.HTTP_200_OK,
    summary="Query evaluation traces",
    description="Filter evaluation traces by model, pass/fail status, minimum cost, or latency.",
)
async def query_traces(
    model_name: str | None = Query(default=None),
    passed: bool | None = Query(default=None),
    min_cost_usd: float | None = Query(default=None, ge=0.0),
    min_latency_ms: float | None = Query(default=None, ge=0.0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[EvaluationTraceRecord]:
    """Query traces matching filter criteria."""
    filters = TraceFilter(
        model_name=model_name,
        passed=passed,
        min_cost_usd=min_cost_usd,
        min_latency_ms=min_latency_ms,
        limit=limit,
    )
    return _tracer.query_traces(filters)


@router.get(
    "/summary",
    response_model=TraceSummary,
    status_code=status.HTTP_200_OK,
    summary="Get observability metrics summary",
    description=(
        "Aggregates total executions, failure rate, mean latency, total tokens, and total cost."
    ),
)
async def get_summary() -> TraceSummary:
    """Retrieve operational summary metrics."""
    return _tracer.get_trace_summary()


@router.get(
    "/reproduce/{run_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get diagnostic reproduction artifact",
    description=(
        "Exports complete execution inputs, prompts, contexts, "
        "and failed metrics for failure replay."
    ),
)
async def reproduce_evaluation(run_id: str) -> dict[str, Any]:
    """Retrieve diagnostic reproduction payload."""
    try:
        return _tracer.reproduce_evaluation(run_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract reproduction payload: {e}",
        ) from e
