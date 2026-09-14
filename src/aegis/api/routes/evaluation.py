"""FastAPI routes for the Evaluation Engine."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from aegis.domain.models.evaluation import (
    EvaluationInput,
    EvaluationResult,
    MetricType,
)
from aegis.services.evaluation_engine import EvaluationEngine

router = APIRouter(prefix="/evaluate", tags=["Evaluation Engine"])

# Global singleton evaluation engine instance for API handling
default_evaluation_engine = EvaluationEngine()


class EvaluateCaseRequest(BaseModel):
    """Payload for evaluating a single question/answer interaction."""

    question: str = Field(..., description="Prompt or query presented to the AI")
    actual_answer: str = Field(..., description="AI-generated response to evaluate")
    expected_answer: str | None = Field(
        default=None, description="Ground truth answer (optional, needed for correctness)"
    )
    retrieved_context: list[str] = Field(
        default_factory=list, description="Retrieved context chunks supporting the answer"
    )
    case_id: str | None = Field(default=None, description="Optional identifier for the test case")
    thresholds: dict[MetricType, float] | None = Field(
        default=None, description="Optional custom pass/fail score thresholds per metric"
    )


class EvaluateBatchRequest(BaseModel):
    """Payload for batch evaluation across multiple interactions."""

    cases: list[EvaluateCaseRequest] = Field(
        ..., min_length=1, description="List of cases to evaluate"
    )
    thresholds: dict[MetricType, float] | None = Field(
        default=None, description="Global thresholds to apply across all cases in this batch"
    )


class EvaluateBatchResponse(BaseModel):
    """Summary and itemized results for a batch evaluation."""

    total_cases: int
    passed_cases: int
    failed_cases: int
    overall_pass_rate: float
    results: list[EvaluationResult]


@router.post(
    "/case",
    response_model=EvaluationResult,
    status_code=status.HTTP_200_OK,
    summary="Evaluate a single AI response",
    description=(
        "Calculates faithfulness, correctness, and relevance scores with pass/fail judgements."
    ),
)
async def evaluate_single_case(payload: EvaluateCaseRequest) -> EvaluationResult:
    """Evaluate one AI response against retrieved context and expected ground truth."""
    try:
        input_data = EvaluationInput(
            question=payload.question,
            actual_answer=payload.actual_answer,
            expected_answer=payload.expected_answer,
            retrieved_context=payload.retrieved_context,
            case_id=payload.case_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    result = await default_evaluation_engine.evaluate_case(
        input_data=input_data,
        thresholds=payload.thresholds,
    )
    return result


@router.post(
    "/batch",
    response_model=EvaluateBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate a batch of AI responses",
    description=(
        "Concurrently runs metric evaluators across multiple test cases and returns an "
        "aggregate report."
    ),
)
async def evaluate_batch_cases(payload: EvaluateBatchRequest) -> EvaluateBatchResponse:
    """Evaluate a batch of test cases."""
    if not payload.cases:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The 'cases' list must not be empty.",
        )

    inputs: list[EvaluationInput] = []
    for case in payload.cases:
        try:
            inputs.append(
                EvaluationInput(
                    question=case.question,
                    actual_answer=case.actual_answer,
                    expected_answer=case.expected_answer,
                    retrieved_context=case.retrieved_context,
                    case_id=case.case_id,
                )
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid case '{case.case_id or case.question[:20]}': {e}",
            ) from e

    results = await default_evaluation_engine.evaluate_batch(
        cases=inputs,
        thresholds=payload.thresholds,
    )

    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)
    pass_rate = round(passed_count / total_count, 4) if total_count > 0 else 0.0

    return EvaluateBatchResponse(
        total_cases=total_count,
        passed_cases=passed_count,
        failed_cases=total_count - passed_count,
        overall_pass_rate=pass_rate,
        results=results,
    )


@router.get(
    "/metrics",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List active evaluation metrics",
    description="Returns metadata and default thresholds for all metrics configured in the engine.",
)
async def get_active_metrics() -> list[dict[str, Any]]:
    """Retrieve metadata about the active evaluation metrics."""
    return default_evaluation_engine.describe_metrics()
