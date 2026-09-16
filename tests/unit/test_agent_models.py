"""Unit tests for Agent domain models (Module 7)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aegis.domain.models.agent import (
    AgentEvaluationResult,
    AgentTrajectory,
    ToolCall,
)


def test_tool_call_valid_creation() -> None:
    """Verify ToolCall model fields and immutability."""
    step = ToolCall(
        name="calculator",
        arguments={"expression": "10 * 4.5"},
        output="45.0",
        error=None,
    )
    assert step.name == "calculator"
    assert step.arguments["expression"] == "10 * 4.5"
    assert step.output == "45.0"
    assert step.error is None

    with pytest.raises(ValidationError):
        step.name = "search"


def test_agent_trajectory_creation() -> None:
    """Verify AgentTrajectory construction."""
    trajectory = AgentTrajectory(
        task="Calculate quarterly tax from revenue data.",
        steps=[
            ToolCall(name="database", arguments={"query": "SELECT revenue FROM q3"}),
            ToolCall(name="calculator", arguments={"expression": "100000 * 0.21"}),
        ],
        final_answer="The calculated tax is $21,000.",
        expected_tools=["database", "calculator"],
        expected_sequence=["database", "calculator"],
    )
    assert len(trajectory.steps) == 2
    assert trajectory.final_answer is not None
    assert trajectory.expected_tools == ["database", "calculator"]


def test_agent_evaluation_result_validation() -> None:
    """Verify AgentEvaluationResult bounds and validation."""
    result = AgentEvaluationResult(
        tool_selection_score=1.0,
        tool_arguments_score=0.9,
        tool_sequence_score=1.0,
        task_completion_score=1.0,
        efficiency_score=1.0,
        unnecessary_steps_count=0,
        overall_score=0.975,
        passed=True,
        diagnostic_reasons=["Optimal execution."],
    )
    assert result.passed is True
    assert result.overall_score == 0.975

    with pytest.raises(ValidationError):
        AgentEvaluationResult(
            tool_selection_score=1.5,  # Out of [0.0, 1.0]
            tool_arguments_score=0.9,
            tool_sequence_score=1.0,
            task_completion_score=1.0,
            efficiency_score=1.0,
            unnecessary_steps_count=0,
            overall_score=1.0,
            passed=True,
        )
