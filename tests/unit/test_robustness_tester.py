"""Unit tests for RobustnessTester service (Module 6)."""

from __future__ import annotations

import pytest

from aegis.domain.models.evaluation import EvaluationInput
from aegis.domain.models.robustness import PerturbationType, RobustnessTestCase
from aegis.services.robustness_tester import RobustnessTester


@pytest.mark.asyncio
async def test_robustness_tester_evaluate_test_case() -> None:
    """Verify single test case comparative evaluation."""
    tester = RobustnessTester(max_allowed_degradation=0.5)

    b_input = EvaluationInput(
        question="What is FastAPI?",
        actual_answer="FastAPI is an asynchronous web framework for Python.",
        expected_answer="FastAPI is an asynchronous Python web framework.",
        retrieved_context=["FastAPI is a modern, high-performance web framework."],
    )
    p_input = EvaluationInput(
        question="What is FatstAPi?",
        actual_answer="FastAPI is an asynchronous web framework for Python.",
        expected_answer="FastAPI is an asynchronous Python web framework.",
        retrieved_context=["FastAPI is a modern, high-performance web framework."],
    )
    test_case = RobustnessTestCase(
        id="rob-test-case-1",
        baseline_input=b_input,
        perturbed_input=p_input,
        perturbation_type=PerturbationType.TYPOS,
    )

    comparison = await tester.evaluate_test_case(test_case)

    assert comparison.test_case_id == "rob-test-case-1"
    assert comparison.perturbation_type == PerturbationType.TYPOS
    assert comparison.baseline_score > 0.0
    assert comparison.perturbed_score > 0.0
    assert comparison.robustness_passed is True


@pytest.mark.asyncio
async def test_robustness_tester_suite_execution() -> None:
    """Verify running multiple perturbation types across baseline inputs."""
    tester = RobustnessTester(max_allowed_degradation=0.5)

    inputs = [
        EvaluationInput(
            question="What is PostgreSQL?",
            actual_answer="PostgreSQL is an open-source relational database system.",
            expected_answer="PostgreSQL is a powerful relational database.",
            retrieved_context=["PostgreSQL is an open-source relational database."],
        )
    ]

    report = await tester.evaluate_suite(
        baseline_inputs=inputs,
        perturbation_types=[
            PerturbationType.TYPOS,
            PerturbationType.MISSING_INFO,
        ],
    )

    assert report.total_tests == 2
    assert report.average_baseline_score > 0.0
    assert report.average_perturbed_score > 0.0
    assert "typos" in report.breakdown_by_type
    assert "missing_info" in report.breakdown_by_type
    assert len(report.comparisons) == 2


@pytest.mark.asyncio
async def test_robustness_tester_empty_suite() -> None:
    """Verify graceful handling when no inputs are provided."""
    tester = RobustnessTester()
    report = await tester.evaluate_suite(baseline_inputs=[], perturbation_types=[])

    assert report.total_tests == 0
    assert report.passed is True
    assert report.robustness_score == 1.0
