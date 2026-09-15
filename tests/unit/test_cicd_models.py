"""Unit tests for CI/CD domain models (Module 11)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aegis.domain.models.cicd import (
    PipelineRunReport,
    QualityGateEvaluation,
    QualityGateThresholds,
)


def test_quality_gate_thresholds_defaults() -> None:
    """Test default threshold parameters."""
    thresholds = QualityGateThresholds()
    assert thresholds.min_faithfulness == 0.90
    assert thresholds.min_correctness == 0.85
    assert thresholds.max_hallucination_rate == 0.05
    assert thresholds.max_latency_p95_ms == 2500.0
    assert thresholds.max_allowed_drop_from_baseline == 0.05


def test_quality_gate_evaluation_valid() -> None:
    """Test valid QualityGateEvaluation instance."""
    eval_gate = QualityGateEvaluation(
        gate_name="Faithfulness",
        target_threshold=0.90,
        actual_value=0.94,
        passed=True,
        status="PASS",
        message="Meets threshold",
    )
    assert eval_gate.passed is True
    assert eval_gate.status == "PASS"


def test_quality_gate_evaluation_frozen() -> None:
    """Test immutability of QualityGateEvaluation."""
    eval_gate = QualityGateEvaluation(
        gate_name="Faithfulness",
        target_threshold=0.90,
        actual_value=0.94,
        passed=True,
        status="PASS",
        message="Meets threshold",
    )
    with pytest.raises(ValidationError):
        eval_gate.passed = False


def test_pipeline_run_report_creation() -> None:
    """Test PipelineRunReport assembly."""
    report = PipelineRunReport(
        pipeline_id="pipe-1",
        git_commit="abcdef",
        branch="feature/test",
        overall_passed=True,
        unit_tests_passed=True,
        integration_tests_passed=True,
        ai_evaluation_passed=True,
        baseline_comparison_passed=True,
        quality_gate_results=[],
        summary="All passed",
    )
    assert report.overall_passed is True
    assert report.pipeline_id == "pipe-1"
