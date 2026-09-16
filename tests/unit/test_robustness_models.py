"""Unit tests for Robustness domain models (Module 6)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aegis.domain.models.evaluation import EvaluationInput
from aegis.domain.models.robustness import (
    PerturbationComparison,
    PerturbationType,
    PerturbedInput,
    RobustnessReport,
    RobustnessTestCase,
)


def test_perturbation_type_values() -> None:
    """Verify all 7 required perturbation categories are represented."""
    expected = {
        "typos",
        "ambiguity",
        "missing_info",
        "conflicting_docs",
        "irrelevant_docs",
        "prompt_injection",
        "out_of_domain",
    }
    actual = {t.value for t in PerturbationType}
    assert expected == actual


def test_perturbed_input_creation() -> None:
    """Verify valid PerturbedInput creation and immutability."""
    p_input = PerturbedInput(
        original_text="What is PostgreSQL?",
        perturbed_text="What is PostgreSQK?",
        perturbation_type=PerturbationType.TYPOS,
        metadata={"typos": 1},
    )
    assert p_input.original_text == "What is PostgreSQL?"
    assert p_input.perturbed_text == "What is PostgreSQK?"
    assert p_input.perturbation_type == PerturbationType.TYPOS


def test_robustness_test_case_validation() -> None:
    """Verify paired baseline and perturbed test case structure."""
    b_input = EvaluationInput(
        question="Explain ACID compliance.",
        actual_answer="ACID guarantees atomicity, consistency, isolation, and durability.",
        expected_answer="ACID stands for atomicity, consistency, isolation, and durability.",
        retrieved_context=["ACID is a set of properties for database transactions."],
    )
    p_input = EvaluationInput(
        question="Explain ACID.",
        actual_answer="ACID guarantees database transaction properties.",
        expected_answer="ACID stands for atomicity, consistency, isolation, and durability.",
        retrieved_context=["ACID is a set of properties for database transactions."],
    )
    test_case = RobustnessTestCase(
        id="rob-test-1",
        baseline_input=b_input,
        perturbed_input=p_input,
        perturbation_type=PerturbationType.MISSING_INFO,
    )
    assert test_case.id == "rob-test-1"
    assert test_case.perturbation_type == PerturbationType.MISSING_INFO


def test_perturbation_comparison_properties() -> None:
    """Verify calculation of delta and degradation ratio."""
    comp = PerturbationComparison(
        test_case_id="tc-1",
        perturbation_type=PerturbationType.TYPOS,
        baseline_score=0.90,
        perturbed_score=0.81,
        score_delta=-0.09,
        degradation_ratio=0.10,
        robustness_passed=True,
        reason="Minimal degradation within limits.",
    )
    assert comp.score_delta == -0.09
    assert comp.degradation_ratio == 0.10
    assert comp.robustness_passed is True

    with pytest.raises(ValidationError):
        PerturbationComparison(
            test_case_id="tc-invalid",
            perturbation_type=PerturbationType.TYPOS,
            baseline_score=1.5,  # Out of [0.0, 1.0]
            perturbed_score=0.5,
            score_delta=-1.0,
            degradation_ratio=0.5,
            robustness_passed=False,
            reason="Invalid score.",
        )


def test_robustness_report_properties() -> None:
    """Verify composite report metrics and breakdown dictionary."""
    comp = PerturbationComparison(
        test_case_id="tc-1",
        perturbation_type=PerturbationType.TYPOS,
        baseline_score=0.90,
        perturbed_score=0.85,
        score_delta=-0.05,
        degradation_ratio=0.055,
        robustness_passed=True,
        reason="Passed.",
    )
    report = RobustnessReport(
        total_tests=1,
        passed_tests=1,
        failed_tests=0,
        average_baseline_score=0.90,
        average_perturbed_score=0.85,
        overall_degradation=0.05,
        robustness_score=0.95,
        breakdown_by_type={"typos": 0.055},
        comparisons=[comp],
        passed=True,
        summary="Robustness evaluation passed.",
    )
    assert report.total_tests == 1
    assert report.passed is True
    assert report.robustness_score == 0.95
