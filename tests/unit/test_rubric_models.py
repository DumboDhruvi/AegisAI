"""Unit tests for rubric domain models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aegis.domain.models.rubric import (
    DEFAULT_5_POINT_RUBRIC,
    GROUNDING_RUBRIC,
    RubricCriterion,
    RubricDefinition,
    RubricScoreResult,
)


def test_rubric_criterion_valid_creation() -> None:
    crit = RubricCriterion(
        score=5,
        label="Completely correct",
        description="Factually accurate in all respects.",
    )
    assert crit.score == 5
    assert crit.label == "Completely correct"
    assert crit.description == "Factually accurate in all respects."


def test_rubric_criterion_rejects_empty_label_or_description() -> None:
    with pytest.raises(ValidationError):
        RubricCriterion(score=5, label="   ", description="Valid description")

    with pytest.raises(ValidationError):
        RubricCriterion(score=5, label="Valid label", description="")


def test_rubric_definition_default_rubric_integrity() -> None:
    rubric = DEFAULT_5_POINT_RUBRIC
    assert rubric.id == "standard-5-point"
    assert rubric.min_score == 0
    assert rubric.max_score == 5
    assert rubric.passing_score == 3
    assert len(rubric.criteria) == 6

    top = rubric.get_criterion_for_score(5)
    assert top is not None
    assert top.label == "Completely correct"

    missing = rubric.get_criterion_for_score(99)
    assert missing is None


def test_rubric_definition_grounding_rubric_integrity() -> None:
    rubric = GROUNDING_RUBRIC
    assert rubric.id == "grounding-3-point"
    assert rubric.min_score == 0
    assert rubric.max_score == 2
    assert len(rubric.criteria) == 3


def test_rubric_definition_rejects_invalid_bounds() -> None:
    c1 = RubricCriterion(score=0, label="Bad", description="Bad")
    c2 = RubricCriterion(score=5, label="Good", description="Good")

    # min_score >= max_score
    with pytest.raises(ValidationError):
        RubricDefinition(
            id="bad-bounds",
            name="Bad",
            description="Desc",
            min_score=5,
            max_score=0,
            criteria=[c1, c2],
        )

    # passing_score out of bounds
    with pytest.raises(ValidationError):
        RubricDefinition(
            id="bad-passing",
            name="Bad",
            description="Desc",
            min_score=0,
            max_score=5,
            passing_score=10,
            criteria=[c1, c2],
        )


def test_rubric_definition_rejects_duplicate_scores() -> None:
    c1 = RubricCriterion(score=3, label="Level 1", description="Desc")
    c2 = RubricCriterion(score=3, label="Level 2", description="Desc")
    with pytest.raises(ValidationError):
        RubricDefinition(
            id="dup-scores",
            name="Duplicates",
            description="Desc",
            min_score=0,
            max_score=5,
            criteria=[c1, c2],
        )


def test_rubric_definition_rejects_out_of_bounds_criteria() -> None:
    c1 = RubricCriterion(score=0, label="Low", description="Desc")
    c2 = RubricCriterion(score=10, label="High", description="Desc")
    with pytest.raises(ValidationError):
        RubricDefinition(
            id="out-of-bounds",
            name="Out of bounds",
            description="Desc",
            min_score=0,
            max_score=5,
            criteria=[c1, c2],
        )


def test_rubric_score_result_validation() -> None:
    res = RubricScoreResult(
        rubric_id="standard-5-point",
        raw_score=4,
        normalized_score=0.8,
        passed=True,
        assigned_label="Minor omission",
        reason="Almost complete, missing date.",
    )
    assert res.raw_score == 4
    assert res.normalized_score == 0.8
    assert res.passed is True
    assert res.assigned_label == "Minor omission"
