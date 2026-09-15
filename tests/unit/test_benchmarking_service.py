"""Unit tests for BenchmarkingService (Module 8)."""

from __future__ import annotations

import pytest

from aegis.domain.models.benchmark import ModelPricing
from aegis.domain.models.evaluation_case import EvaluationCase
from aegis.services.benchmarking_service import (
    BenchmarkingService,
    estimate_tokens,
)


def test_estimate_tokens() -> None:
    """Verify character-to-token approximation."""
    assert estimate_tokens("") == 0
    assert estimate_tokens("hi") >= 1
    assert estimate_tokens("AegisAI evaluation platform") >= 4


def test_cost_calculation() -> None:
    """Verify accurate USD token cost calculation."""
    service = BenchmarkingService()
    # gpt-4o: $2.50 / 1M prompt, $10.00 / 1M completion
    # 10,000 prompt tokens = $0.025, 1,000 completion tokens = $0.010 -> total $0.035
    cost = service.calculate_cost("gpt-4o", prompt_tokens=10000, completion_tokens=1000)
    assert cost == 0.035


def test_register_and_list_pricing() -> None:
    """Verify custom pricing registration."""
    service = BenchmarkingService()
    custom_pricing = ModelPricing(
        model_id="custom-fine-tune",
        input_cost_per_million=5.00,
        output_cost_per_million=20.00,
    )
    service.register_pricing(custom_pricing)
    catalog = service.get_pricing_catalog()

    assert "custom-fine-tune" in catalog
    assert catalog["custom-fine-tune"].input_cost_per_million == 5.00


@pytest.mark.asyncio
async def test_run_benchmark_comparison() -> None:
    """Verify multi-model benchmarking run across test cases."""
    service = BenchmarkingService()
    cases = [
        EvaluationCase(
            id="case-1",
            question="What is PostgreSQL?",
            expected_answer="PostgreSQL is an open-source relational database.",
            context=["PostgreSQL is a powerful open-source relational database."],
        ),
        EvaluationCase(
            id="case-2",
            question="What is FastAPI?",
            expected_answer="FastAPI is an asynchronous web framework for Python.",
            context=["FastAPI is a modern, fast web framework for building APIs."],
        ),
    ]

    report = await service.run_benchmark(
        dataset_name="tech-stack-eval",
        cases=cases,
    )

    assert report.dataset_name == "tech-stack-eval"
    assert len(report.evaluated_models) == 2
    assert "mock-model-a" in report.model_summaries
    assert "mock-model-b" in report.model_summaries

    summary_a = report.model_summaries["mock-model-a"]
    assert summary_a.total_cases == 2
    assert summary_a.mean_accuracy > 0.0
    assert summary_a.mean_latency_ms >= 0.0
    assert summary_a.total_cost_usd > 0.0
    assert report.winner_model_id in {"mock-model-a", "mock-model-b"}
    assert len(report.recommendations) >= 1
