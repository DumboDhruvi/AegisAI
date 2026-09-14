"""Unit tests for EvaluationCase and dataset domain models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aegis.domain.models.evaluation_case import (
    DatasetValidationResult,
    EvaluationCase,
    EvaluationDataset,
    RejectedCase,
)


def test_valid_evaluation_case_creation() -> None:
    """Ensure a valid evaluation case initializes properly with expected fields."""
    case = EvaluationCase(
        id="case-101",
        question="What is the return policy?",
        expected_answer="Customers can return items within 30 days.",
        context=["Items may be returned within 30 days of purchase for a full refund."],
        rubric={"must_include": ["30 days", "full refund"], "weight": 1.0},
        tags=["Policy", "Refund", "policy"],  # Should normalize to ['policy', 'refund']
    )
    assert case.id == "case-101"
    assert case.question == "What is the return policy?"
    assert case.expected_answer == "Customers can return items within 30 days."
    assert len(case.context) == 1
    assert case.tags == ["policy", "refund"]
    assert case.rubric["weight"] == 1.0


@pytest.mark.parametrize("empty_value", ["", "   ", "\n\t"])
def test_evaluation_case_rejects_empty_id(empty_value: str) -> None:
    """Ensure empty or whitespace-only id raises ValidationError."""
    with pytest.raises(ValidationError, match="Field 'id' must not be empty"):
        EvaluationCase(
            id=empty_value,
            question="Valid question",
            expected_answer="Valid answer",
        )


@pytest.mark.parametrize("empty_value", ["", "   ", "\t"])
def test_evaluation_case_rejects_empty_question(empty_value: str) -> None:
    """Ensure empty or whitespace-only question raises ValidationError."""
    with pytest.raises(ValidationError, match="Field 'question' must not be empty"):
        EvaluationCase(
            id="valid-id",
            question=empty_value,
            expected_answer="Valid answer",
        )


@pytest.mark.parametrize("empty_value", ["", "   "])
def test_evaluation_case_rejects_empty_expected_answer(empty_value: str) -> None:
    """Ensure empty or whitespace-only expected_answer raises ValidationError."""
    with pytest.raises(ValidationError, match="Field 'expected_answer' must not be empty"):
        EvaluationCase(
            id="valid-id",
            question="Valid question",
            expected_answer=empty_value,
        )


def test_evaluation_case_filters_empty_context_chunks() -> None:
    """Ensure empty or whitespace context chunks are filtered out."""
    case = EvaluationCase(
        id="case-102",
        question="What is the shipping cost?",
        expected_answer="Shipping is free on orders over $50.",
        context=["Shipping is free over $50.", "   ", ""],
    )
    assert case.context == ["Shipping is free over $50."]


def test_evaluation_case_immutability() -> None:
    """Ensure EvaluationCase is frozen and immutable."""
    case = EvaluationCase(
        id="case-103",
        question="Question",
        expected_answer="Answer",
    )
    with pytest.raises(ValidationError):
        # Trying to assign to frozen instance should fail at runtime
        case.question = "Modified Question"


def test_dataset_validation_result_counts() -> None:
    """Ensure validation result properties calculate correct counts and validity."""
    case = EvaluationCase(
        id="case-1",
        question="Q1",
        expected_answer="A1",
    )
    rejected = RejectedCase(
        raw_identifier="bad-1",
        raw_data={"question": "No ID or answer"},
        errors=["Field 'id' is required", "Field 'expected_answer' is required"],
    )

    result = DatasetValidationResult(
        valid_cases=[case],
        rejected_cases=[rejected],
        total_count=2,
    )
    assert not result.is_fully_valid
    assert result.valid_count == 1
    assert result.rejected_count == 1


def test_evaluation_dataset_methods() -> None:
    """Ensure dataset lookup and tag filtering work accurately."""
    case1 = EvaluationCase(
        id="case-1",
        question="Q1",
        expected_answer="A1",
        tags=["rag", "finance"],
    )
    case2 = EvaluationCase(
        id="case-2",
        question="Q2",
        expected_answer="A2",
        tags=["rag", "legal"],
    )
    dataset = EvaluationDataset(name="test-set", version="v1", cases=[case1, case2])

    assert len(dataset) == 2
    assert dataset.get_case("case-1") == case1
    assert dataset.get_case("case-999") is None

    rag_cases = dataset.filter_by_tag("RAG")
    assert len(rag_cases) == 2

    legal_cases = dataset.filter_by_tag("legal")
    assert len(legal_cases) == 1
    assert legal_cases[0].id == "case-2"
