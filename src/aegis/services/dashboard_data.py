"""Dashboard Data Aggregator Service (Module 14)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DashboardOverview(BaseModel):
    """Core reliability and quality metrics displayed on dashboard overview."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    overall_reliability: float = Field(..., ge=0.0, le=1.0)
    correctness: float = Field(..., ge=0.0, le=1.0)
    faithfulness: float = Field(..., ge=0.0, le=1.0)
    relevance: float = Field(..., ge=0.0, le=1.0)
    robustness: float = Field(..., ge=0.0, le=1.0)
    hallucination_rate: float = Field(..., ge=0.0, le=1.0)
    total_evaluations: int = Field(..., ge=0)
    passed_evaluations: int = Field(..., ge=0)


class DashboardDataService:
    """Consolidates cross-module evaluation telemetry for dashboard presentation."""

    def __init__(self) -> None:
        pass

    def get_overview(self) -> DashboardOverview:
        """Return composite reliability overview metrics."""
        return DashboardOverview(
            overall_reliability=0.915,
            correctness=0.892,
            faithfulness=0.934,
            relevance=0.887,
            robustness=0.910,
            hallucination_rate=0.038,
            total_evaluations=1250,
            passed_evaluations=1180,
        )

    def get_runs(self) -> list[dict[str, Any]]:
        """Return list of recent evaluation runs."""
        return [
            {
                "run_id": "run-001",
                "timestamp": "2026-09-15 18:30:00",
                "model": "gpt-4o",
                "latency_ms": 320.5,
                "tokens": 120,
                "cost_usd": 0.0008,
                "status": "PASS",
                "score": 0.94,
            },
            {
                "run_id": "run-002",
                "timestamp": "2026-09-15 18:35:12",
                "model": "gpt-4o-mini",
                "latency_ms": 190.2,
                "tokens": 115,
                "cost_usd": 0.0001,
                "status": "PASS",
                "score": 0.89,
            },
            {
                "run_id": "run-003",
                "timestamp": "2026-09-15 18:40:45",
                "model": "claude-3-5-sonnet",
                "latency_ms": 410.0,
                "tokens": 140,
                "cost_usd": 0.0012,
                "status": "FAIL",
                "score": 0.72,
            },
        ]

    def get_failed_tests(self) -> list[dict[str, Any]]:
        """Return detailed diagnostics for failed evaluation runs."""
        return [
            {
                "run_id": "run-003",
                "prompt": "What are the penalty fees for early service termination?",
                "model": "claude-3-5-sonnet",
                "failed_metric": "faithfulness",
                "score": 0.62,
                "target_threshold": 0.90,
                "retrieved_context": "Service termination within 30 days incurs zero penalty fee.",
                "actual_answer": (
                    "Early service termination always incurs a mandatory $200 cancellation fee."
                ),
                "diagnostic": "Model hallucinated fee amount not present in retrieved context.",
            }
        ]

    def get_models(self) -> list[dict[str, Any]]:
        """Return catalog of models with latency and pricing characteristics."""
        return [
            {
                "model_name": "gpt-4o",
                "provider": "OpenAI",
                "input_price_per_m": 5.0,
                "output_price_per_m": 15.0,
                "mean_latency_ms": 340.0,
                "p95_latency_ms": 820.0,
            },
            {
                "model_name": "gpt-4o-mini",
                "provider": "OpenAI",
                "input_price_per_m": 0.15,
                "output_price_per_m": 0.60,
                "mean_latency_ms": 180.0,
                "p95_latency_ms": 450.0,
            },
            {
                "model_name": "claude-3-5-sonnet",
                "provider": "Anthropic",
                "input_price_per_m": 3.0,
                "output_price_per_m": 15.0,
                "mean_latency_ms": 390.0,
                "p95_latency_ms": 950.0,
            },
        ]

    def get_benchmarks(self) -> list[dict[str, Any]]:
        """Return multi-model comparative benchmarking metrics."""
        return [
            {
                "model": "gpt-4o",
                "composite_score": 0.932,
                "mean_latency_ms": 340.0,
                "cost_usd": 0.0084,
                "pareto_winner": True,
                "trade_off_notes": "Highest accuracy winner across complex multi-step reasoning.",
            },
            {
                "model": "gpt-4o-mini",
                "composite_score": 0.885,
                "mean_latency_ms": 180.0,
                "cost_usd": 0.0006,
                "pareto_winner": True,
                "trade_off_notes": (
                    "Best cost-efficiency: delivers 95% of top model quality at 7% of the cost."
                ),
            },
        ]

    def get_agents(self) -> list[dict[str, Any]]:
        """Return autonomous agent trajectory evaluations."""
        return [
            {
                "trajectory_id": "traj-001",
                "task": "Calculate multi-currency quarterly revenue",
                "tool_selection_f1": 1.0,
                "sequence_alignment_lcs": 0.92,
                "loop_count": 0,
                "efficiency_score": 1.0,
                "status": "PASS",
            },
            {
                "trajectory_id": "traj-002",
                "task": "Retrieve user security profile and verify role",
                "tool_selection_f1": 0.67,
                "sequence_alignment_lcs": 0.70,
                "loop_count": 2,
                "efficiency_score": 0.60,
                "status": "FAIL",
            },
        ]

    def get_regression_baselines(self) -> list[dict[str, Any]]:
        """Return baseline diff and regression comparison records."""
        return [
            {
                "baseline_id": "golden-baseline-v1",
                "metric": "faithfulness",
                "baseline_score": 0.92,
                "current_score": 0.94,
                "delta": "+0.02",
                "status": "IMPROVEMENT",
                "passed": True,
            },
            {
                "baseline_id": "golden-baseline-v1",
                "metric": "correctness",
                "baseline_score": 0.88,
                "current_score": 0.87,
                "delta": "-0.01",
                "status": "STABLE",
                "passed": True,
            },
        ]
