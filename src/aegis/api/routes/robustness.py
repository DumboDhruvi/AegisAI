"""FastAPI routes for Robustness and Adversarial Testing (Module 6)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from aegis.domain.models.evaluation import EvaluationInput
from aegis.domain.models.robustness import (
    PerturbationComparison,
    PerturbationType,
    PerturbedInput,
    RobustnessReport,
)
from aegis.services.perturbation_engine import PerturbationEngine
from aegis.services.robustness_tester import RobustnessTester

router = APIRouter(prefix="/robustness", tags=["Robustness Testing"])

_engine = PerturbationEngine()
_tester = RobustnessTester(perturbation_engine=_engine)


class PerturbTextRequest(BaseModel):
    """Request payload to apply a specific synthetic perturbation to text."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1, description="Input string to perturb")
    perturbation_type: PerturbationType = Field(..., description="Target perturbation category")
    typo_rate: float = Field(default=0.1, ge=0.0, le=1.0, description="Typo error rate")


class EvaluateRobustnessCaseRequest(BaseModel):
    """Request payload to run comparative robustness analysis on a single input."""

    model_config = ConfigDict(extra="forbid")

    baseline_input: EvaluationInput = Field(..., description="Unperturbed base input")
    perturbation_type: PerturbationType = Field(..., description="Perturbation category to test")
    max_degradation: float | None = Field(
        default=0.25, ge=0.0, le=1.0, description="Max acceptable performance degradation"
    )


class EvaluateRobustnessSuiteRequest(BaseModel):
    """Request payload to execute a full robustness benchmark suite."""

    model_config = ConfigDict(extra="forbid")

    baseline_inputs: list[EvaluationInput] = Field(
        ..., min_length=1, description="List of baseline evaluation inputs"
    )
    perturbation_types: list[PerturbationType] | None = Field(
        default=None, description="Categories of perturbations to run (runs all if omitted)"
    )
    max_degradation: float | None = Field(
        default=0.25, ge=0.0, le=1.0, description="Max acceptable performance degradation"
    )


@router.post(
    "/perturb",
    response_model=PerturbedInput,
    status_code=status.HTTP_200_OK,
    summary="Perturb text input",
    description="Generates a synthetic or adversarial perturbation of an input prompt.",
)
async def perturb_text(payload: PerturbTextRequest) -> PerturbedInput:
    """Generate a perturbed variant of the provided text."""
    try:
        p_type = payload.perturbation_type
        if p_type == PerturbationType.TYPOS:
            return _engine.apply_typos(payload.text, typo_rate=payload.typo_rate)
        elif p_type == PerturbationType.AMBIGUITY:
            return _engine.apply_ambiguity(payload.text)
        elif p_type == PerturbationType.MISSING_INFO:
            return _engine.apply_missing_info(payload.text)
        elif p_type == PerturbationType.PROMPT_INJECTION:
            return _engine.inject_prompt_injection(payload.text)
        elif p_type == PerturbationType.OUT_OF_DOMAIN:
            return _engine.generate_out_of_domain(payload.text)
        else:
            return PerturbedInput(
                original_text=payload.text,
                perturbed_text=payload.text,
                perturbation_type=p_type,
                metadata={"note": "Context-level perturbation, query unchanged"},
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perturb text: {e}",
        ) from e


@router.post(
    "/evaluate-case",
    response_model=PerturbationComparison,
    status_code=status.HTTP_200_OK,
    summary="Evaluate single robustness case",
    description="Evaluates quality degradation between baseline and perturbed inputs.",
)
async def evaluate_robustness_case(
    payload: EvaluateRobustnessCaseRequest,
) -> PerturbationComparison:
    """Run comparative evaluation on a single baseline input against a perturbation."""
    try:
        test_case = _engine.create_robustness_test_case(
            baseline_input=payload.baseline_input,
            perturbation_type=payload.perturbation_type,
            case_id="api-rob-case-1",
        )
        return await _tester.evaluate_test_case(test_case, max_degradation=payload.max_degradation)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Robustness case evaluation failed: {e}",
        ) from e


@router.post(
    "/evaluate-suite",
    response_model=RobustnessReport,
    status_code=status.HTTP_200_OK,
    summary="Evaluate robustness suite",
    description="Executes a full comparative robustness benchmark across multiple inputs.",
)
async def evaluate_robustness_suite(
    payload: EvaluateRobustnessSuiteRequest,
) -> RobustnessReport:
    """Execute a full comparative robustness test suite."""
    try:
        return await _tester.evaluate_suite(
            baseline_inputs=payload.baseline_inputs,
            perturbation_types=payload.perturbation_types,
            max_degradation=payload.max_degradation,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Robustness suite evaluation failed: {e}",
        ) from e
