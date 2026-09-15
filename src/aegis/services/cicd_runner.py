"""CI/CD Quality Gate Runner and Evaluation Pipeline (Module 11)."""

from __future__ import annotations

import logging
from typing import Any

from aegis.domain.models.cicd import (
    PipelineRunReport,
    QualityGateEvaluation,
    QualityGateThresholds,
)
from aegis.services.regression_engine import BaselineStore, RegressionEngine

logger = logging.getLogger(__name__)


class CicdRunner:
    """Orchestrates automated AI quality gates and regression diffing in CI/CD pipelines."""

    def __init__(
        self,
        thresholds: QualityGateThresholds | None = None,
        regression_engine: RegressionEngine | None = None,
    ) -> None:
        self.thresholds = thresholds or QualityGateThresholds()
        self.regression_engine = regression_engine or RegressionEngine(
            baseline_store=BaselineStore()
        )

    def evaluate_quality_gates(self, metrics: dict[str, float]) -> list[QualityGateEvaluation]:
        """Evaluate observed metric values against configured minimum and maximum limits."""
        evaluations: list[QualityGateEvaluation] = []

        # 1. Faithfulness (minimum bound)
        if "faithfulness" in metrics:
            val = metrics["faithfulness"]
            passed = val >= self.thresholds.min_faithfulness
            evaluations.append(
                QualityGateEvaluation(
                    gate_name="Faithfulness",
                    target_threshold=self.thresholds.min_faithfulness,
                    actual_value=val,
                    passed=passed,
                    status="PASS" if passed else "FAIL",
                    message=(
                        f"Faithfulness {val:.3f} {'meets or exceeds' if passed else 'is below'} "
                        f"minimum threshold {self.thresholds.min_faithfulness:.3f}."
                    ),
                )
            )

        # 2. Correctness (minimum bound)
        if "correctness" in metrics:
            val = metrics["correctness"]
            passed = val >= self.thresholds.min_correctness
            evaluations.append(
                QualityGateEvaluation(
                    gate_name="Correctness",
                    target_threshold=self.thresholds.min_correctness,
                    actual_value=val,
                    passed=passed,
                    status="PASS" if passed else "FAIL",
                    message=(
                        f"Correctness {val:.3f} {'meets or exceeds' if passed else 'is below'} "
                        f"minimum threshold {self.thresholds.min_correctness:.3f}."
                    ),
                )
            )

        # 3. Hallucination Rate (maximum bound)
        if "hallucination_rate" in metrics:
            val = metrics["hallucination_rate"]
            passed = val <= self.thresholds.max_hallucination_rate
            evaluations.append(
                QualityGateEvaluation(
                    gate_name="Hallucination Rate",
                    target_threshold=self.thresholds.max_hallucination_rate,
                    actual_value=val,
                    passed=passed,
                    status="PASS" if passed else "FAIL",
                    message=(
                        f"Hallucination rate {val:.3f} "
                        f"{'is within' if passed else 'exceeds maximum permissible'} "
                        f"limit {self.thresholds.max_hallucination_rate:.3f}."
                    ),
                )
            )

        # 4. Latency P95 (maximum bound in ms)
        if "latency_p95_ms" in metrics:
            val = metrics["latency_p95_ms"]
            passed = val <= self.thresholds.max_latency_p95_ms
            evaluations.append(
                QualityGateEvaluation(
                    gate_name="P95 Latency",
                    target_threshold=self.thresholds.max_latency_p95_ms,
                    actual_value=val,
                    passed=passed,
                    status="PASS" if passed else "FAIL",
                    message=(
                        f"P95 Latency {val:.1f}ms "
                        f"{'is within' if passed else 'exceeds maximum permissible'} "
                        f"budget {self.thresholds.max_latency_p95_ms:.1f}ms."
                    ),
                )
            )

        # 5. Custom Metric Minimums
        for metric_name, target in self.thresholds.custom_metric_minimums.items():
            if metric_name in metrics:
                val = metrics[metric_name]
                passed = val >= target
                evaluations.append(
                    QualityGateEvaluation(
                        gate_name=metric_name,
                        target_threshold=target,
                        actual_value=val,
                        passed=passed,
                        status="PASS" if passed else "FAIL",
                        message=(
                            f"Custom metric '{metric_name}' {val:.3f} "
                            f"{'meets' if passed else 'fails'} target {target:.3f}."
                        ),
                    )
                )

        return evaluations

    def run_pipeline_check(
        self,
        pipeline_id: str,
        git_commit: str,
        branch: str,
        unit_tests_passed: bool,
        integration_tests_passed: bool,
        current_metrics: dict[str, float],
        baseline_id: str | None = None,
        current_version: str = "candidate",
        metadata: dict[str, Any] | None = None,
    ) -> PipelineRunReport:
        """Evaluate a complete CI/CD candidate build across code tests, gates, and baseline."""
        gate_results = self.evaluate_quality_gates(current_metrics)
        ai_evaluation_passed = all(gate.passed for gate in gate_results)

        regression_report = None
        baseline_comparison_passed = True

        if baseline_id is not None:
            try:
                regression_report = self.regression_engine.compare(
                    baseline_id=baseline_id,
                    current_version=current_version,
                    current_metrics=current_metrics,
                    max_allowed_drop=self.thresholds.max_allowed_drop_from_baseline,
                )
                baseline_comparison_passed = regression_report.passed
            except Exception as e:
                logger.error("Baseline comparison against '%s' failed: %s", baseline_id, e)
                baseline_comparison_passed = False

        overall_passed = (
            unit_tests_passed
            and integration_tests_passed
            and ai_evaluation_passed
            and baseline_comparison_passed
        )

        failures: list[str] = []
        if not unit_tests_passed:
            failures.append("Unit tests failed")
        if not integration_tests_passed:
            failures.append("Integration tests failed")
        if not ai_evaluation_passed:
            failed_gates = [g.gate_name for g in gate_results if not g.passed]
            failures.append(f"AI quality gates failed: {', '.join(failed_gates)}")
        if not baseline_comparison_passed:
            failures.append(f"Baseline regression detected against '{baseline_id}'")

        if overall_passed:
            summary = (
                f"CI/CD PIPELINE PASSED ({pipeline_id}): Unit tests, integration tests, "
                f"{len(gate_results)} AI quality gates, and baseline verification all passed."
            )
        else:
            summary = f"CI/CD PIPELINE FAILED ({pipeline_id}): {'; '.join(failures)}."

        return PipelineRunReport(
            pipeline_id=pipeline_id,
            git_commit=git_commit,
            branch=branch,
            overall_passed=overall_passed,
            unit_tests_passed=unit_tests_passed,
            integration_tests_passed=integration_tests_passed,
            ai_evaluation_passed=ai_evaluation_passed,
            baseline_comparison_passed=baseline_comparison_passed,
            quality_gate_results=gate_results,
            regression_report=regression_report,
            metadata=metadata or {},
            summary=summary,
        )
