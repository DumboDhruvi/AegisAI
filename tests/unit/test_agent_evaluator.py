"""Unit tests for AgentTrajectoryEvaluator and MockAgentToolRegistry (Module 7)."""

from __future__ import annotations

from aegis.domain.models.agent import AgentTrajectory, ToolCall
from aegis.services.agent_evaluator import (
    AgentTrajectoryEvaluator,
    MockAgentToolRegistry,
)


def test_mock_agent_tool_registry() -> None:
    """Verify mock tool execution behavior for standard suite."""
    calc_out = MockAgentToolRegistry.execute("calculator", {"expression": "12 * 8"})
    assert calc_out == "96"

    db_out = MockAgentToolRegistry.execute(
        "database", {"query": "SELECT * FROM users", "table": "users"}
    )
    assert "users" in db_out

    search_out = MockAgentToolRegistry.execute("search", {"query": "FastAPI"})
    assert "FastAPI" in search_out

    web_out = MockAgentToolRegistry.execute("web_search", {"query": "current weather"})
    assert "current weather" in web_out

    unknown = MockAgentToolRegistry.execute("unregistered_tool", {})
    assert "Unknown tool" in unknown


def test_agent_evaluator_optimal_trajectory() -> None:
    """Verify evaluation of a correct, efficient agent trajectory."""
    evaluator = AgentTrajectoryEvaluator()
    trajectory = AgentTrajectory(
        task="Find database user count and calculate average per department.",
        steps=[
            ToolCall(
                name="database",
                arguments={"query": "SELECT COUNT(*) FROM users", "table": "users"},
            ),
            ToolCall(name="calculator", arguments={"expression": "150 / 5"}),
        ],
        final_answer="There are 150 users across 5 departments, averaging 30 per department.",
        expected_tools=["database", "calculator"],
        expected_sequence=["database", "calculator"],
    )

    result = evaluator.evaluate_trajectory(trajectory)

    assert result.tool_selection_score == 1.0
    assert result.tool_arguments_score == 1.0
    assert result.tool_sequence_score == 1.0
    assert result.task_completion_score == 1.0
    assert result.efficiency_score == 1.0
    assert result.unnecessary_steps_count == 0
    assert result.overall_score >= 0.9
    assert result.passed is True


def test_agent_evaluator_unnecessary_steps_penalty() -> None:
    """Verify duplicate redundant calls penalize efficiency score."""
    evaluator = AgentTrajectoryEvaluator()
    trajectory = AgentTrajectory(
        task="Look up product price.",
        steps=[
            ToolCall(name="search", arguments={"query": "laptop price"}),
            # Redundant duplicate calls
            ToolCall(name="search", arguments={"query": "laptop price"}),
            ToolCall(name="search", arguments={"query": "laptop price"}),
        ],
        final_answer="The laptop costs $999.",
        expected_tools=["search"],
    )

    result = evaluator.evaluate_trajectory(trajectory)

    assert result.unnecessary_steps_count == 2
    assert result.efficiency_score < 1.0


def test_agent_evaluator_missing_final_answer() -> None:
    """Verify trajectory without final answer fails task completion."""
    evaluator = AgentTrajectoryEvaluator()
    trajectory = AgentTrajectory(
        task="Fetch stock price.",
        steps=[ToolCall(name="web_search", arguments={"query": "AAPL price"})],
        final_answer=None,  # Incomplete
    )

    result = evaluator.evaluate_trajectory(trajectory)

    assert result.task_completion_score == 0.0
    assert result.passed is False


def test_agent_evaluator_invalid_arguments() -> None:
    """Verify empty or missing required arguments reduce argument score."""
    evaluator = AgentTrajectoryEvaluator()
    trajectory = AgentTrajectory(
        task="Search information.",
        steps=[
            # Missing "query" argument
            ToolCall(name="search", arguments={})
        ],
        final_answer="Found nothing.",
    )

    result = evaluator.evaluate_trajectory(trajectory)
    assert result.tool_arguments_score == 0.0


def test_agent_evaluator_out_of_order_sequence() -> None:
    """Verify inverted tool invocation sequence reduces sequence score."""
    evaluator = AgentTrajectoryEvaluator()
    trajectory = AgentTrajectory(
        task="Calculate then store.",
        steps=[
            ToolCall(name="database", arguments={"table": "results"}),
            ToolCall(name="calculator", arguments={"expression": "5 + 5"}),
        ],
        final_answer="Done.",
        expected_sequence=["calculator", "database"],
    )

    result = evaluator.evaluate_trajectory(trajectory)
    # LCS is 1 out of 2 -> sequence score should be 0.5
    assert result.tool_sequence_score == 0.5
