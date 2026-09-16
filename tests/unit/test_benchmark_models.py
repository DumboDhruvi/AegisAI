"""Unit tests for Benchmarking domain models (Module 8)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aegis.domain.models.benchmark import (
    BenchmarkComparisonReport,
    ModelBenchmarkSummary,
    ModelExecutionResult,
    ModelPricing,
)


def test_model_pricing_validation() -> None:
    """Verify ModelPricing creation and bounds."""
    pricing = ModelPricing(
        model_id="gpt-4o",
        input_cost_per_million=2.50,
        output_cost_per_million=10.00,
    )
    assert pricing.model_id == "gpt-4o"
    assert pricing.input_cost_per_million == 2.50
    assert pricing.output_cost_per_million == 10.00

    with pytest.raises(ValidationError):
        ModelPricing(
            model_id="invalid",
            input_cost_per_million=-1.0,  # Negative cost disallowed
            output_cost_per_million=1.0,
        )


def test_model_execution_result_properties() -> None:
    """Verify ModelExecutionResult field constraints."""
    res = ModelExecutionResult(
        model_id="claude-3-5-sonnet",
        case_id="case-101",
        actual_answer="PostgreSQL adheres to ACID transactions.",
        accuracy_score=0.95,
        faithfulness_score=0.98,
        relevance_score=0.92,
        hallucination_rate=0.0,
        latency_ms=350.5,
        prompt_tokens=120,
        completion_tokens=45,
        total_tokens=165,
        cost_usd=0.001035,
    )
    assert res.total_tokens == 165
    assert res.accuracy_score == 0.95
    assert res.cost_usd > 0.0


def test_model_benchmark_summary_and_report() -> None:
    """Verify ModelBenchmarkSummary and BenchmarkComparisonReport."""
    summary = ModelBenchmarkSummary(
        model_id="mock-model-a",
        total_cases=10,
        mean_accuracy=0.92,
        mean_faithfulness=0.95,
        mean_relevance=0.88,
        mean_hallucination_rate=0.03,
        mean_latency_ms=250.0,
        p95_latency_ms=450.0,
        total_tokens=2500,
        total_cost_usd=0.025,
        composite_quality_score=0.915,
    )
    report = BenchmarkComparisonReport(
        benchmark_id="bench-001",
        dataset_name="enterprise-rag-eval",
        evaluated_models=["mock-model-a"],
        model_summaries={"mock-model-a": summary},
        winner_model_id="mock-model-a",
        recommendations=["mock-model-a performed optimally."],
    )
    assert report.benchmark_id == "bench-001"
    assert report.winner_model_id == "mock-model-a"
    assert "mock-model-a" in report.model_summaries
