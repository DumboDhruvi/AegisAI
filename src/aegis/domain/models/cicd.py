"""Domain models for Automated CI/CD AI Quality Gates (Module 11)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from aegis.domain.models.regression import RegressionReport


class QualityGateThresholds(BaseModel):
    """Configurable quality threshold limits for CI/CD automated gates."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    min_faithfulness: float = Field(
        default=0.90, ge=0.0, le=1.0, description="Minimum acceptable faithfulness score"
    )
    min_correctness: float = Field(
        default=0.85, ge=0.0, le=1.0, description="Minimum acceptable correctness score"
    )
    max_hallucination_rate: float = Field(
        default=0.05, ge=0.0, le=1.0, description="Maximum permissible hallucination rate"
    )
    max_latency_p95_ms: float = Field(
        default=2500.0, ge=0.0, description="Maximum permissible P95 latency in milliseconds"
    )
    custom_metric_minimums: dict[str, float] = Field(
        default_factory=dict, description="Arbitrary additional metric minimum thresholds"
    )
    max_allowed_drop_from_baseline: float = Field(
        default=0.05, ge=0.0, le=1.0, description="Permissible drop tolerance vs baseline"
    )


class QualityGateEvaluation(BaseModel):
    """Detailed evaluation result for an individual quality gate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    gate_name: str = Field(..., description="Name of the evaluated quality gate")
    target_threshold: float = Field(..., description="Required threshold cutoff")
    actual_value: float = Field(..., description="Observed metric value in current run")
    passed: bool = Field(..., description="True if gate criteria were satisfied")
    status: str = Field(..., description="PASS or FAIL")
    message: str = Field(..., description="Diagnostic assessment of gate result")


class PipelineRunReport(BaseModel):
    """Comprehensive CI/CD evaluation pipeline execution report."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pipeline_id: str = Field(..., description="Unique CI/CD pipeline run identifier")
    git_commit: str = Field(..., description="Git commit hash evaluated")
    branch: str = Field(..., description="Source git branch name")
    overall_passed: bool = Field(
        ..., description="True if all tests, quality gates, and baselines passed"
    )
    unit_tests_passed: bool = Field(..., description="Result of unit test suite")
    integration_tests_passed: bool = Field(..., description="Result of integration test suite")
    ai_evaluation_passed: bool = Field(..., description="Result of AI quality gates")
    baseline_comparison_passed: bool = Field(
        ..., description="Result of baseline regression diff check"
    )
    quality_gate_results: list[QualityGateEvaluation] = Field(
        default_factory=list, description="Per-gate evaluation results"
    )
    regression_report: RegressionReport | None = Field(
        default=None, description="Detailed baseline diff report if baseline check was executed"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary pipeline context and environment info"
    )
    summary: str = Field(..., description="Executive verdict of CI/CD pipeline run")
