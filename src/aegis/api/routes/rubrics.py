"""FastAPI routes for managing and evaluating rubrics."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from aegis.domain.models.evaluation import EvaluationInput
from aegis.domain.models.rubric import RubricDefinition, RubricScoreResult
from aegis.services.rubric_engine import RubricEngine

router = APIRouter(prefix="/rubrics", tags=["Rubric Engine"])

# Global singleton rubric engine instance for the API
default_rubric_engine = RubricEngine()


class EvaluateRubricRequest(BaseModel):
    """Payload for evaluating an interaction against a specific rubric."""

    rubric_id: str = Field(default="standard-5-point", description="ID of the rubric to apply")
    question: str = Field(..., description="Prompt or question presented to the AI")
    actual_answer: str = Field(..., description="AI response to evaluate")
    expected_answer: str | None = Field(default=None, description="Optional ground truth answer")
    retrieved_context: list[str] = Field(
        default_factory=list, description="Retrieved context chunks supporting the answer"
    )
    passing_score_override: int | None = Field(
        default=None, description="Optional custom passing threshold score"
    )


@router.get(
    "",
    response_model=list[RubricDefinition],
    status_code=status.HTTP_200_OK,
    summary="List all registered rubrics",
    description="Returns metadata, score bounds, and criteria bands for all active rubrics.",
)
def list_registered_rubrics() -> list[RubricDefinition]:
    """List all available system and custom rubrics."""
    return default_rubric_engine.list_rubrics()


@router.get(
    "/{rubric_id}",
    response_model=RubricDefinition,
    status_code=status.HTTP_200_OK,
    summary="Get rubric details",
    description="Retrieve full criteria bands and thresholds for a specific rubric ID.",
)
def get_rubric_details(rubric_id: str) -> RubricDefinition:
    """Retrieve details of a specific rubric."""
    rubric = default_rubric_engine.get_rubric(rubric_id)
    if not rubric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rubric '{rubric_id}' not found.",
        )
    return rubric


@router.post(
    "",
    response_model=RubricDefinition,
    status_code=status.HTTP_201_CREATED,
    summary="Register a custom rubric",
    description="Adds a new rubric definition with custom criteria bands to the engine.",
)
def register_custom_rubric(rubric: RubricDefinition) -> RubricDefinition:
    """Register a custom evaluation rubric."""
    existing = default_rubric_engine.get_rubric(rubric.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A rubric with ID '{rubric.id}' is already registered.",
        )
    default_rubric_engine.register_rubric(rubric)
    return rubric


@router.post(
    "/evaluate",
    response_model=RubricScoreResult,
    status_code=status.HTTP_200_OK,
    summary="Evaluate with a rubric",
    description=(
        "Applies rubric criteria to evaluate an interaction and returns score, "
        "band label, and rationale."
    ),
)
async def evaluate_with_rubric(payload: EvaluateRubricRequest) -> RubricScoreResult:
    """Evaluate an AI interaction against a rubric."""
    try:
        input_data = EvaluationInput(
            question=payload.question,
            actual_answer=payload.actual_answer,
            expected_answer=payload.expected_answer,
            retrieved_context=payload.retrieved_context,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    try:
        result = await default_rubric_engine.evaluate_with_rubric(
            input_data=input_data,
            rubric_id=payload.rubric_id,
            passing_score_override=payload.passing_score_override,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return result
