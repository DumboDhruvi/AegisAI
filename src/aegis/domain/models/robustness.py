"""Domain models for Robustness and Adversarial Testing (Module 6)."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from aegis.domain.models.evaluation import EvaluationInput


class PerturbationType(str, Enum):
    """Categories of synthetic and adversarial perturbations."""

    TYPOS = "typos"
    AMBIGUITY = "ambiguity"
    MISSING_INFO = "missing_info"
    CONFLICTING_DOCS = "conflicting_docs"
    IRRELEVANT_DOCS = "irrelevant_docs"
    PROMPT_INJECTION = "prompt_injection"
    OUT_OF_DOMAIN = "out_of_domain"


class PerturbedInput(BaseModel):
    """Result of perturbing an input prompt or context."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    original_text: str = Field(..., description="Unperturbed base text")
    perturbed_text: str = Field(..., description="Perturbed variant text")
    perturbation_type: PerturbationType = Field(..., description="Type of perturbation applied")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Diagnostic parameters used in perturbation"
    )


class RobustnessTestCase(BaseModel):
    """Paired baseline and perturbed evaluation input for comparative robustness testing."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., description="Identifier for the robustness test pair")
    baseline_input: EvaluationInput = Field(..., description="Normal unperturbed input")
    perturbed_input: EvaluationInput = Field(..., description="Perturbed / adversarial input")
    perturbation_type: PerturbationType = Field(..., description="Applied perturbation category")


class PerturbationComparison(BaseModel):
    """Comparative performance delta between baseline and perturbed execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    test_case_id: str = Field(..., description="ID of evaluated test case")
    perturbation_type: PerturbationType = Field(..., description="Perturbation category")
    baseline_score: float = Field(
        ..., ge=0.0, le=1.0, description="Normalized score on baseline input"
    )
    perturbed_score: float = Field(
        ..., ge=0.0, le=1.0, description="Normalized score on perturbed input"
    )
    score_delta: float = Field(
        ..., description="Difference in score (perturbed_score - baseline_score)"
    )
    degradation_ratio: float = Field(
        ..., ge=0.0, le=1.0, description="Relative drop in quality [0.0, 1.0]"
    )
    robustness_passed: bool = Field(
        ..., description="Whether degradation is within acceptable threshold"
    )
    reason: str = Field(..., description="Diagnostic justification for robustness decision")


class RobustnessReport(BaseModel):
    """Composite robustness evaluation report comparing normal vs adversarial performance."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_tests: int = Field(..., ge=0, description="Total number of evaluated comparisons")
    passed_tests: int = Field(..., ge=0, description="Number of tests passing robustness gates")
    failed_tests: int = Field(..., ge=0, description="Number of tests suffering severe degradation")
    average_baseline_score: float = Field(
        ..., ge=0.0, le=1.0, description="Mean score across unperturbed baselines"
    )
    average_perturbed_score: float = Field(
        ..., ge=0.0, le=1.0, description="Mean score across perturbed evaluations"
    )
    overall_degradation: float = Field(
        ..., description="Mean score drop between baseline and perturbed runs"
    )
    robustness_score: float = Field(
        ..., ge=0.0, le=1.0, description="Composite robustness index [0.0, 1.0]"
    )
    breakdown_by_type: dict[str, float] = Field(
        default_factory=dict, description="Mean degradation ratio grouped by perturbation type"
    )
    comparisons: list[PerturbationComparison] = Field(
        default_factory=list, description="Per-test comparison details"
    )
    passed: bool = Field(
        ..., description="Whether overall robustness meets required enterprise threshold"
    )
    summary: str = Field(..., description="Executive diagnostic summary of robustness findings")
