"""Unit tests for CicdRunner and CLI entrypoint (Module 11)."""

from __future__ import annotations

from aegis.cli.ci_gate import main as cli_main
from aegis.domain.models.cicd import QualityGateThresholds
from aegis.domain.models.regression import BaselineRecord
from aegis.services.cicd_runner import CicdRunner
from aegis.services.regression_engine import BaselineStore, RegressionEngine


def test_evaluate_quality_gates_pass() -> None:
    """Test all quality gates passing when metrics exceed targets."""
    runner = CicdRunner()
    metrics = {
        "faithfulness": 0.95,
        "correctness": 0.90,
        "hallucination_rate": 0.02,
        "latency_p95_ms": 1100.0,
    }
    gates = runner.evaluate_quality_gates(metrics)
    assert len(gates) == 4
    assert all(g.passed for g in gates)


def test_evaluate_quality_gates_failures() -> None:
    """Test quality gates failing when metrics violate thresholds."""
    runner = CicdRunner()
    metrics = {
        "faithfulness": 0.82,  # Target >= 0.90 -> FAIL
        "correctness": 0.75,  # Target >= 0.85 -> FAIL
        "hallucination_rate": 0.12,  # Target <= 0.05 -> FAIL
        "latency_p95_ms": 3200.0,  # Target <= 2500 -> FAIL
    }
    gates = runner.evaluate_quality_gates(metrics)
    assert len(gates) == 4
    assert all(not g.passed for g in gates)
    assert all(g.status == "FAIL" for g in gates)


def test_custom_metric_minimums() -> None:
    """Test custom metric evaluation in quality gates."""
    thresholds = QualityGateThresholds(
        custom_metric_minimums={"context_recall": 0.80, "grounding_score": 0.85}
    )
    runner = CicdRunner(thresholds=thresholds)
    metrics = {"context_recall": 0.82, "grounding_score": 0.70}
    gates = runner.evaluate_quality_gates(metrics)
    recall_gate = next(g for g in gates if g.gate_name == "context_recall")
    grounding_gate = next(g for g in gates if g.gate_name == "grounding_score")
    assert recall_gate.passed is True
    assert grounding_gate.passed is False


def test_run_pipeline_check_all_passed() -> None:
    """Test complete CI/CD candidate evaluation when everything passes."""
    runner = CicdRunner()
    metrics = {
        "faithfulness": 0.94,
        "correctness": 0.89,
        "hallucination_rate": 0.01,
    }
    report = runner.run_pipeline_check(
        pipeline_id="pipe-pass-1",
        git_commit="abc1234",
        branch="main",
        unit_tests_passed=True,
        integration_tests_passed=True,
        current_metrics=metrics,
    )
    assert report.overall_passed is True
    assert report.ai_evaluation_passed is True
    assert "CI/CD PIPELINE PASSED" in report.summary


def test_run_pipeline_check_code_tests_fail() -> None:
    """Test pipeline failure when unit tests fail."""
    runner = CicdRunner()
    metrics = {"faithfulness": 0.95, "correctness": 0.90}
    report = runner.run_pipeline_check(
        pipeline_id="pipe-code-fail",
        git_commit="abc1234",
        branch="main",
        unit_tests_passed=False,
        integration_tests_passed=True,
        current_metrics=metrics,
    )
    assert report.overall_passed is False
    assert "Unit tests failed" in report.summary


def test_run_pipeline_check_with_baseline_comparison() -> None:
    """Test CI/CD evaluation including automated baseline diffing."""
    store = BaselineStore()
    baseline = BaselineRecord(
        baseline_id="golden-v1",
        dataset_version="v1",
        model_id="gpt-4o-mini",
        metrics={"faithfulness": 0.90, "correctness": 0.85},
    )
    store.save_baseline(baseline)
    engine = RegressionEngine(baseline_store=store)
    runner = CicdRunner(regression_engine=engine)

    # Candidate has faithfulness drop of 0.15 (exceeds 0.05 allowed drop)
    metrics = {
        "faithfulness": 0.75,
        "correctness": 0.88,
    }
    report = runner.run_pipeline_check(
        pipeline_id="pipe-regression-fail",
        git_commit="abc1234",
        branch="main",
        unit_tests_passed=True,
        integration_tests_passed=True,
        current_metrics=metrics,
        baseline_id="golden-v1",
    )
    assert report.overall_passed is False
    assert report.baseline_comparison_passed is False
    assert report.regression_report is not None
    assert "Baseline regression detected" in report.summary


def test_cli_ci_gate_pass_and_fail(capsys: object) -> None:
    """Test CLI ci_gate main entrypoint exits with correct codes."""
    # Passing arguments
    pass_exit = cli_main(
        [
            "--faithfulness",
            "0.95",
            "--correctness",
            "0.90",
            "--hallucination-rate",
            "0.02",
        ]
    )
    assert pass_exit == 0

    # Failing arguments
    fail_exit = cli_main(
        [
            "--faithfulness",
            "0.70",
            "--min-faithfulness",
            "0.90",
        ]
    )
    assert fail_exit == 1
