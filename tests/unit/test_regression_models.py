"""Unit tests for Regression and Baseline domain models (Module 9)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aegis.domain.models.regression import (
    BaselineRecord,
    RegressionComparison,
    RegressionReport,
    RegressionStatus,
)


def test_baseline_record_instantiation() -> None:
    """Test valid BaselineRecord creation and serialization."""
    record = BaselineRecord(
        baseline_id="base-v1.0.0",
        dataset_version="golden-v1",
        model_id="gpt-4o-mini",
        metrics={"faithfulness": 0.92, "answer_relevance": 0.88},
        metadata={"git_commit": "abc1234"},
    )
    assert record.baseline_id == "base-v1.0.0"
    assert record.dataset_version == "golden-v1"
    assert record.metrics["faithfulness"] == 0.92
    assert record.metadata["git_commit"] == "abc1234"
    assert record.created_at is not None

    dump = record.model_dump()
    assert dump["baseline_id"] == "base-v1.0.0"


def test_baseline_record_frozen() -> None:
    """Test immutability of BaselineRecord."""
    record = BaselineRecord(
        baseline_id="base-v1",
        dataset_version="v1",
        model_id="gpt-4o-mini",
        metrics={"faithfulness": 0.90},
    )
    with pytest.raises(ValidationError):
        record.baseline_id = "base-v2"


def test_regression_comparison_valid() -> None:
    """Test valid RegressionComparison creation."""
    comp = RegressionComparison(
        metric_name="faithfulness",
        baseline_score=0.90,
        current_score=0.92,
        delta=0.02,
        max_allowed_drop=0.05,
        status=RegressionStatus.IMPROVEMENT,
        passed=True,
        diagnostic="Improved by 0.02",
    )
    assert comp.status == RegressionStatus.IMPROVEMENT
    assert comp.passed is True
    assert comp.delta == 0.02


def test_regression_comparison_bounds() -> None:
    """Test score bounds validation [0.0, 1.0]."""
    with pytest.raises(ValidationError):
        RegressionComparison(
            metric_name="faithfulness",
            baseline_score=-0.1,  # Invalid < 0.0
            current_score=0.9,
            delta=1.0,
            status=RegressionStatus.IMPROVEMENT,
            passed=True,
            diagnostic="Invalid",
        )

    with pytest.raises(ValidationError):
        RegressionComparison(
            metric_name="faithfulness",
            baseline_score=0.9,
            current_score=1.5,  # Invalid > 1.0
            delta=0.6,
            status=RegressionStatus.IMPROVEMENT,
            passed=True,
            diagnostic="Invalid",
        )


def test_regression_report_valid() -> None:
    """Test RegressionReport aggregation."""
    comp = RegressionComparison(
        metric_name="faithfulness",
        baseline_score=0.90,
        current_score=0.82,
        delta=-0.08,
        max_allowed_drop=0.05,
        status=RegressionStatus.REGRESSION,
        passed=False,
        diagnostic="Dropped significantly",
    )
    report = RegressionReport(
        baseline_id="base-v1",
        current_version="v2.0",
        has_regression=True,
        passed=False,
        comparisons=[comp],
        summary="QUALITY GATE FAILED: Regression detected in faithfulness.",
    )
    assert report.has_regression is True
    assert report.passed is False
    assert len(report.comparisons) == 1
