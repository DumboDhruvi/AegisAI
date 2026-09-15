"""FastAPI routes for Automated CI/CD AI Quality Gates (Module 11)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from aegis.domain.models.cicd import (
    PipelineRunReport,
    QualityGateEvaluation,
    QualityGateThresholds,
)
from aegis.services.cicd_runner import CicdRunner

router = APIRouter(prefix="/cicd", tags=["CI/CD Pipeline"])

_runner = CicdRunner()


class PipelineCheckRequest(BaseModel):
    """Payload to trigger an end-to-end CI/CD candidate build evaluation."""

    model_config = ConfigDict(extra="forbid")

    pipeline_id: str = Field(..., min_length=1, description="CI Pipeline Run ID")
    git_commit: str = Field(..., min_length=1, description="Git commit SHA")
    branch: str = Field(..., min_length=1, description="Branch name")
    unit_tests_passed: bool = Field(default=True, description="Unit test suite status")
    integration_tests_passed: bool = Field(
        default=True, description="Integration test suite status"
    )
    current_metrics: dict[str, float] = Field(
        ..., description="Observed evaluation metrics in candidate build"
    )
    baseline_id: str | None = Field(default=None, description="Optional baseline snapshot ID")
    current_version: str = Field(default="candidate", description="Version label")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Pipeline context")


@router.post(
    "/evaluate-gates",
    response_model=list[QualityGateEvaluation],
    status_code=status.HTTP_200_OK,
    summary="Evaluate quality gates",
    description="Evaluates observed metrics against configured AI quality gate thresholds.",
)
async def evaluate_gates(metrics: dict[str, float]) -> list[QualityGateEvaluation]:
    """Evaluate individual quality gates against target thresholds."""
    try:
        return _runner.evaluate_quality_gates(metrics)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quality gate evaluation failed: {e}",
        ) from e


@router.post(
    "/run-pipeline-check",
    response_model=PipelineRunReport,
    status_code=status.HTTP_200_OK,
    summary="Run full CI/CD pipeline check",
    description="Evaluates code tests, AI quality gates, and optional baseline diffs.",
)
async def run_pipeline_check(payload: PipelineCheckRequest) -> PipelineRunReport:
    """Execute end-to-end CI/CD pipeline verification."""
    try:
        return _runner.run_pipeline_check(
            pipeline_id=payload.pipeline_id,
            git_commit=payload.git_commit,
            branch=payload.branch,
            unit_tests_passed=payload.unit_tests_passed,
            integration_tests_passed=payload.integration_tests_passed,
            current_metrics=payload.current_metrics,
            baseline_id=payload.baseline_id,
            current_version=payload.current_version,
            metadata=payload.metadata,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CI/CD pipeline check failed: {e}",
        ) from e


@router.get(
    "/default-thresholds",
    response_model=QualityGateThresholds,
    status_code=status.HTTP_200_OK,
    summary="Get default quality gate thresholds",
    description="Returns standard minimum and maximum thresholds for CI/CD gates.",
)
async def get_default_thresholds() -> QualityGateThresholds:
    """Retrieve active quality gate thresholds."""
    return _runner.thresholds
