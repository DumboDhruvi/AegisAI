"""Unit tests for LLM-as-a-Judge evaluators."""

from __future__ import annotations

import json

import pytest

from aegis.domain.models.evaluation import EvaluationInput, MetricType
from aegis.infrastructure.llm import MockLlmProvider
from aegis.services.evaluators.llm_judge import (
    LlmAnswerRelevanceJudge,
    LlmCorrectnessJudge,
    LlmFaithfulnessJudge,
)


@pytest.mark.asyncio
async def test_llm_faithfulness_judge_with_valid_json() -> None:
    mock_response = json.dumps(
        {
            "score": 0.95,
            "passed": True,
            "reason": "All claims are strictly derived from the retrieved documents.",
        }
    )
    llm = MockLlmProvider(fixed_response=mock_response)
    judge = LlmFaithfulnessJudge(llm_provider=llm, default_threshold=0.8)

    inp = EvaluationInput(
        question="What is AegisAI?",
        actual_answer="AegisAI is an AI evaluation platform.",
        retrieved_context=["AegisAI is an enterprise platform for AI evaluation."],
    )
    res = await judge.evaluate(inp)
    assert res.metric_type == MetricType.FAITHFULNESS
    assert res.score == 0.95
    assert res.passed is True
    assert "All claims are strictly derived" in res.reason


@pytest.mark.asyncio
async def test_llm_faithfulness_judge_missing_context() -> None:
    llm = MockLlmProvider()
    judge = LlmFaithfulnessJudge(llm_provider=llm)

    inp = EvaluationInput(
        question="What is AegisAI?",
        actual_answer="AegisAI is an AI evaluation platform.",
        retrieved_context=[],
    )
    res = await judge.evaluate(inp)
    assert res.score == 0.0
    assert res.passed is False
    assert "No retrieved context was provided" in res.reason


@pytest.mark.asyncio
async def test_llm_correctness_judge_with_markdown_fences() -> None:
    mock_payload = {
        "score": 0.88,
        "passed": True,
        "reason": "The answer aligns accurately with ground truth.",
    }
    raw_markdown = f"```json\n{json.dumps(mock_payload)}\n```"
    llm = MockLlmProvider(fixed_response=raw_markdown)
    judge = LlmCorrectnessJudge(llm_provider=llm, default_threshold=0.7)

    inp = EvaluationInput(
        question="Who created Python?",
        actual_answer="Guido van Rossum in 1991.",
        expected_answer="Python was conceived by Guido van Rossum.",
    )
    res = await judge.evaluate(inp)
    assert res.metric_type == MetricType.CORRECTNESS
    assert res.score == 0.88
    assert res.passed is True


@pytest.mark.asyncio
async def test_llm_correctness_judge_missing_expected_answer() -> None:
    llm = MockLlmProvider()
    judge = LlmCorrectnessJudge(llm_provider=llm)

    inp = EvaluationInput(
        question="Who created Python?",
        actual_answer="Guido van Rossum.",
        expected_answer=None,
    )
    res = await judge.evaluate(inp)
    assert res.score == 0.0
    assert res.passed is False
    assert "Expected answer (ground truth) is required" in res.reason


@pytest.mark.asyncio
async def test_llm_answer_relevance_judge_with_fallback_text() -> None:
    # Model generates text with "Score: 0.85" but not JSON
    raw_text = "Score: 0.85\nThe model clearly answered the user question with relevant details."
    llm = MockLlmProvider(fixed_response=raw_text)
    judge = LlmAnswerRelevanceJudge(llm_provider=llm, default_threshold=0.7)

    inp = EvaluationInput(
        question="How do I configure logging?",
        actual_answer="Set LOG_LEVEL=DEBUG in your .env file.",
    )
    res = await judge.evaluate(inp)
    assert res.metric_type == MetricType.ANSWER_RELEVANCE
    assert res.score == 0.85
    assert res.passed is True
