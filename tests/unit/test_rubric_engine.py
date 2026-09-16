"""Unit tests for the RubricEngine service."""

from __future__ import annotations

import json

import pytest

from aegis.domain.models.evaluation import EvaluationInput
from aegis.domain.models.rubric import (
    RubricCriterion,
    RubricDefinition,
)
from aegis.infrastructure.llm import MockLlmProvider
from aegis.services.rubric_engine import RubricEngine


@pytest.mark.asyncio
async def test_rubric_engine_llm_evaluation_success() -> None:
    mock_payload = json.dumps(
        {
            "score": 5,
            "reason": "The response is comprehensive and fully factually accurate.",
        }
    )
    llm = MockLlmProvider(fixed_response=mock_payload)
    engine = RubricEngine(llm_provider=llm)

    inp = EvaluationInput(
        question="What is AegisAI?",
        actual_answer="AegisAI is an enterprise reliability and evaluation platform.",
        expected_answer="AegisAI evaluates and benchmarks AI systems.",
    )
    result = await engine.evaluate_with_rubric(inp, rubric_id="standard-5-point")
    assert result.rubric_id == "standard-5-point"
    assert result.raw_score == 5
    assert result.normalized_score == 1.0
    assert result.passed is True
    assert result.assigned_label == "Completely correct"
    assert "comprehensive" in result.reason


@pytest.mark.asyncio
async def test_rubric_engine_llm_evaluation_regex_fallback() -> None:
    # Model generates plaintext "Score: 2 - Contains noticeable mistakes"
    raw_text = "Score: 2\nThe explanation contains significant errors regarding the mechanism."
    llm = MockLlmProvider(fixed_response=raw_text)
    engine = RubricEngine(llm_provider=llm)

    inp = EvaluationInput(
        question="How does sliding window work?",
        actual_answer="It deletes the file when done.",
    )
    result = await engine.evaluate_with_rubric(inp, rubric_id="standard-5-point")
    assert result.raw_score == 2
    assert result.normalized_score == 0.4
    assert result.passed is False
    assert result.assigned_label == "Significant error"


@pytest.mark.asyncio
async def test_rubric_engine_deterministic_fallback_with_ground_truth() -> None:
    # No LLM supplied
    engine = RubricEngine(llm_provider=None)

    inp = EvaluationInput(
        question="What is Python?",
        actual_answer="Python is a programming language.",
        expected_answer="Python is a high level programming language.",
    )
    result = await engine.evaluate_with_rubric(inp, rubric_id="standard-5-point")
    assert result.raw_score >= 3
    assert result.passed is True


@pytest.mark.asyncio
async def test_rubric_engine_deterministic_fallback_no_context() -> None:
    engine = RubricEngine(llm_provider=None)
    inp = EvaluationInput(
        question="What is Python?",
        actual_answer="An animal.",
        expected_answer=None,
        retrieved_context=[],
    )
    result = await engine.evaluate_with_rubric(inp, rubric_id="standard-5-point")
    assert result.raw_score == 0
    assert result.passed is False
    assert result.assigned_label == "Incorrect / hallucinated"


@pytest.mark.asyncio
async def test_rubric_engine_passing_score_override() -> None:
    mock_payload = json.dumps({"score": 4, "reason": "Good."})
    llm = MockLlmProvider(fixed_response=mock_payload)
    engine = RubricEngine(llm_provider=llm)

    inp = EvaluationInput(
        question="Test",
        actual_answer="Test",
    )
    # Default passing score is 3 -> score 4 passes
    res1 = await engine.evaluate_with_rubric(inp, rubric_id="standard-5-point")
    assert res1.passed is True

    # Override passing score to 5 -> score 4 fails
    res2 = await engine.evaluate_with_rubric(
        inp, rubric_id="standard-5-point", passing_score_override=5
    )
    assert res2.passed is False


def test_rubric_engine_registration_and_retrieval() -> None:
    engine = RubricEngine()
    custom_rubric = RubricDefinition(
        id="custom-3-scale",
        name="Custom 3-Point Scale",
        description="Simple ternary evaluation",
        min_score=1,
        max_score=3,
        passing_score=2,
        criteria=[
            RubricCriterion(score=3, label="Good", description="Good"),
            RubricCriterion(score=2, label="Ok", description="Ok"),
            RubricCriterion(score=1, label="Bad", description="Bad"),
        ],
    )
    engine.register_rubric(custom_rubric)
    assert engine.get_rubric("custom-3-scale") == custom_rubric
    all_rubrics = engine.list_rubrics()
    assert len(all_rubrics) >= 3


@pytest.mark.asyncio
async def test_rubric_engine_raises_for_unregistered_rubric() -> None:
    engine = RubricEngine()
    inp = EvaluationInput(question="Q", actual_answer="A")
    with pytest.raises(KeyError, match="not registered"):
        await engine.evaluate_with_rubric(inp, rubric_id="non-existent")
