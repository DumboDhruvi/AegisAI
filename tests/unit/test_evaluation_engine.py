"""Unit tests for the core EvaluationEngine service."""

from __future__ import annotations

import pytest

from aegis.domain.models.evaluation import EvaluationInput, MetricType
from aegis.services.evaluation_engine import EvaluationEngine


@pytest.mark.asyncio
async def test_evaluation_engine_default_suite_all_pass() -> None:
    engine = EvaluationEngine()
    inp = EvaluationInput(
        question="What is AegisAI?",
        actual_answer="AegisAI is an enterprise reliability evaluation platform.",
        expected_answer="AegisAI is an enterprise evaluation platform.",
        retrieved_context=["AegisAI is an enterprise reliability and evaluation platform for AI."],
    )
    result = await engine.evaluate_case(inp)

    assert result.passed is True
    assert result.composite_score >= 0.7
    assert len(result.metrics) == 3

    types = {m.metric_type for m in result.metrics}
    assert types == {
        MetricType.FAITHFULNESS,
        MetricType.CORRECTNESS,
        MetricType.ANSWER_RELEVANCE,
    }


@pytest.mark.asyncio
async def test_evaluation_engine_custom_weights() -> None:
    # Heavy weight on faithfulness
    weights = {
        MetricType.FAITHFULNESS: 3.0,
        MetricType.CORRECTNESS: 1.0,
        MetricType.ANSWER_RELEVANCE: 1.0,
    }
    engine = EvaluationEngine(weights=weights)

    inp = EvaluationInput(
        question="What is the capital of France?",
        actual_answer="Paris is the capital of France.",
        expected_answer="Paris",
        retrieved_context=["Paris is the capital and most populous city of France."],
    )
    result = await engine.evaluate_case(inp)
    assert result.composite_score > 0.0


@pytest.mark.asyncio
async def test_evaluation_engine_custom_threshold_override() -> None:
    engine = EvaluationEngine()
    inp = EvaluationInput(
        question="What is Python?",
        actual_answer="Python is a language.",
        expected_answer="Python is a general purpose programming language.",
        retrieved_context=["Python is a language."],
    )
    # Impose an extremely high threshold of 0.99
    thresholds = {MetricType.CORRECTNESS: 0.99}
    result = await engine.evaluate_case(inp, thresholds=thresholds)

    correctness_metric = next(m for m in result.metrics if m.metric_type == MetricType.CORRECTNESS)
    assert correctness_metric.threshold == 0.99
    assert correctness_metric.passed is False
    assert result.passed is False


@pytest.mark.asyncio
async def test_evaluation_engine_batch_evaluation() -> None:
    engine = EvaluationEngine()
    cases = [
        EvaluationInput(
            question=f"Question {i}",
            actual_answer=f"Answer {i}",
            expected_answer=f"Answer {i}",
            retrieved_context=[f"Context for answer {i}"],
            case_id=f"case-{i}",
        )
        for i in range(5)
    ]
    results = await engine.evaluate_batch(cases)
    assert len(results) == 5
    for idx, r in enumerate(results):
        assert r.case_id == f"case-{idx}"


def test_evaluation_engine_describe_metrics() -> None:
    engine = EvaluationEngine()
    descriptors = engine.describe_metrics()
    assert len(descriptors) == 3
    metric_names = [d["metric_type"] for d in descriptors]
    assert "faithfulness" in metric_names
    assert "correctness" in metric_names
    assert "answer_relevance" in metric_names
