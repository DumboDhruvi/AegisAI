"""Unit tests for deterministic metric evaluators."""

from __future__ import annotations

import pytest

from aegis.domain.models.evaluation import EvaluationInput, MetricType
from aegis.services.evaluators.deterministic import (
    F1CorrectnessEvaluator,
    KeywordRelevanceEvaluator,
    LexicalFaithfulnessEvaluator,
)


@pytest.mark.asyncio
async def test_f1_correctness_exact_match() -> None:
    evaluator = F1CorrectnessEvaluator(default_threshold=0.7)
    inp = EvaluationInput(
        question="What is Python?",
        actual_answer="Python is a high-level programming language.",
        expected_answer="Python is a high-level programming language.",
    )
    result = await evaluator.evaluate(inp)
    assert result.metric_type == MetricType.CORRECTNESS
    assert result.score == 1.0
    assert result.passed is True
    assert "F1 correctness score of 1.0000" in result.reason


@pytest.mark.asyncio
async def test_f1_correctness_partial_match() -> None:
    evaluator = F1CorrectnessEvaluator(default_threshold=0.5)
    inp = EvaluationInput(
        question="What is Python?",
        actual_answer="Python is an interpreted programming language created by Guido.",
        expected_answer="Python is a programming language.",
    )
    result = await evaluator.evaluate(inp)
    assert result.score > 0.0
    assert result.score < 1.0
    assert result.passed is True


@pytest.mark.asyncio
async def test_f1_correctness_zero_overlap() -> None:
    evaluator = F1CorrectnessEvaluator(default_threshold=0.5)
    inp = EvaluationInput(
        question="What is Python?",
        actual_answer="Elephants live in Africa and India.",
        expected_answer="Python is a programming language.",
    )
    result = await evaluator.evaluate(inp)
    assert result.score == 0.0
    assert result.passed is False
    assert "No common tokens found" in result.reason


@pytest.mark.asyncio
async def test_f1_correctness_missing_expected_answer() -> None:
    evaluator = F1CorrectnessEvaluator()
    inp = EvaluationInput(
        question="What is Python?",
        actual_answer="A programming language.",
        expected_answer=None,
    )
    result = await evaluator.evaluate(inp)
    assert result.score == 0.0
    assert result.passed is False
    assert "Expected answer (ground truth) is missing" in result.reason


@pytest.mark.asyncio
async def test_lexical_faithfulness_fully_grounded() -> None:
    evaluator = LexicalFaithfulnessEvaluator(default_threshold=0.7)
    inp = EvaluationInput(
        question="What database does AegisAI use?",
        actual_answer="AegisAI uses PostgreSQL with pgvector for vector search.",
        retrieved_context=[
            "AegisAI is built on PostgreSQL with pgvector extension for similarity search."
        ],
    )
    result = await evaluator.evaluate(inp)
    assert result.metric_type == MetricType.FAITHFULNESS
    assert result.score == 1.0
    assert result.passed is True


@pytest.mark.asyncio
async def test_lexical_faithfulness_hallucinated_claim() -> None:
    evaluator = LexicalFaithfulnessEvaluator(default_threshold=0.7)
    inp = EvaluationInput(
        question="What database does AegisAI use?",
        actual_answer="AegisAI uses MongoDB and Redis for document caching.",
        retrieved_context=["AegisAI is built on PostgreSQL with pgvector extension enabled."],
    )
    result = await evaluator.evaluate(inp)
    assert result.score == 0.0
    assert result.passed is False
    assert "below threshold" in result.reason


@pytest.mark.asyncio
async def test_lexical_faithfulness_missing_context() -> None:
    evaluator = LexicalFaithfulnessEvaluator()
    inp = EvaluationInput(
        question="What database does AegisAI use?",
        actual_answer="PostgreSQL with pgvector.",
        retrieved_context=[],
    )
    result = await evaluator.evaluate(inp)
    assert result.score == 0.0
    assert result.passed is False
    assert "No retrieved context provided" in result.reason


@pytest.mark.asyncio
async def test_keyword_relevance_high_coverage() -> None:
    evaluator = KeywordRelevanceEvaluator(default_threshold=0.6)
    inp = EvaluationInput(
        question="How does sliding window chunking prevent boundary loss?",
        actual_answer=(
            "Sliding window chunking includes overlap between chunks to prevent boundary loss."
        ),
    )
    result = await evaluator.evaluate(inp)
    assert result.metric_type == MetricType.ANSWER_RELEVANCE
    assert result.score >= 0.6
    assert result.passed is True


@pytest.mark.asyncio
async def test_keyword_relevance_low_coverage() -> None:
    evaluator = KeywordRelevanceEvaluator(default_threshold=0.6)
    inp = EvaluationInput(
        question="How does sliding window chunking prevent boundary loss?",
        actual_answer="It is sunny in California today.",
    )
    result = await evaluator.evaluate(inp)
    assert result.score == 0.0
    assert result.passed is False
    assert "Missing key concepts" in result.reason
