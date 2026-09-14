"""Unit tests for evaluation domain models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aegis.domain.models.evaluation import (
    EvaluationInput,
    EvaluationResult,
    MetricResult,
    MetricType,
)


def test_evaluation_input_valid_creation() -> None:
    inp = EvaluationInput(
        question="What is RAG?",
        actual_answer="Retrieval-Augmented Generation.",
        expected_answer="RAG stands for Retrieval-Augmented Generation.",
        retrieved_context=["Retrieval-Augmented Generation (RAG) is a technique."],
        case_id="case-101",
    )
    assert inp.question == "What is RAG?"
    assert inp.actual_answer == "Retrieval-Augmented Generation."
    assert inp.expected_answer == "RAG stands for Retrieval-Augmented Generation."
    assert len(inp.retrieved_context) == 1
    assert inp.case_id == "case-101"


def test_evaluation_input_rejects_empty_question() -> None:
    with pytest.raises(ValidationError):
        EvaluationInput(
            question="   ",
            actual_answer="Valid answer",
        )


def test_evaluation_input_rejects_empty_actual_answer() -> None:
    with pytest.raises(ValidationError):
        EvaluationInput(
            question="Valid question",
            actual_answer="\t\n  ",
        )


def test_evaluation_input_cleans_context_and_strips() -> None:
    inp = EvaluationInput(
        question="Test",
        actual_answer="Answer",
        retrieved_context=["  Valid chunk  ", "", "   ", "Second chunk"],
    )
    assert inp.retrieved_context == ["Valid chunk", "Second chunk"]


def test_evaluation_input_immutability() -> None:
    inp = EvaluationInput(
        question="Question",
        actual_answer="Answer",
    )
    with pytest.raises(ValidationError):
        inp.question = "New Question"


def test_metric_result_validation() -> None:
    res = MetricResult(
        metric_type=MetricType.CORRECTNESS,
        score=0.85678,
        passed=True,
        threshold=0.7,
        reason="Good match",
        details={"info": "ok"},
    )
    assert res.score == 0.8568
    assert res.passed is True
    assert res.threshold == 0.7


def test_metric_result_score_bounds() -> None:
    with pytest.raises(ValidationError):
        MetricResult(
            metric_type=MetricType.FAITHFULNESS,
            score=1.5,
            passed=True,
            reason="Invalid score",
        )

    with pytest.raises(ValidationError):
        MetricResult(
            metric_type=MetricType.FAITHFULNESS,
            score=-0.1,
            passed=False,
            reason="Invalid score",
        )


def test_evaluation_result_properties() -> None:
    m1 = MetricResult(
        metric_type=MetricType.FAITHFULNESS,
        score=0.9,
        passed=True,
        reason="Faithful",
    )
    m2 = MetricResult(
        metric_type=MetricType.CORRECTNESS,
        score=0.8,
        passed=True,
        reason="Correct",
    )
    eval_res = EvaluationResult(
        case_id="c-1",
        question="Q?",
        actual_answer="Ans",
        passed=True,
        composite_score=0.85,
        metrics=[m1, m2],
    )
    assert eval_res.passed is True
    assert eval_res.composite_score == 0.85
    assert len(eval_res.metrics) == 2
    assert eval_res.evaluated_at is not None
