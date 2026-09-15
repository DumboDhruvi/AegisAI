"""Domain models for Autonomous Agent trajectory and tool call evaluation (Module 7)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolCall(BaseModel):
    """Represents a single tool invocation step within an agent execution trace."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(..., min_length=1, description="Tool name (e.g. 'search', 'calculator')")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Dictionary of arguments passed to the tool"
    )
    output: str | None = Field(default=None, description="Output returned by tool invocation")
    error: str | None = Field(default=None, description="Error message if tool execution failed")


class AgentTrajectory(BaseModel):
    """An execution trajectory recording an agent's multi-step problem solving process."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    task: str = Field(..., min_length=1, description="User instruction or goal for the agent")
    steps: list[ToolCall] = Field(
        default_factory=list, description="Ordered sequence of tool calls executed"
    )
    final_answer: str | None = Field(
        default=None, description="Final natural language answer or completion message"
    )
    expected_tools: list[str] | None = Field(
        default=None, description="List of tool names expected to be selected"
    )
    expected_sequence: list[str] | None = Field(
        default=None, description="Expected exact or ordered sequence of tool names"
    )
    expected_arguments: dict[str, dict[str, Any]] | None = Field(
        default=None, description="Expected arguments per tool name"
    )


class AgentEvaluationResult(BaseModel):
    """Evaluation breakdown analyzing agent tool usage, efficiency, and task completion."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tool_selection_score: float = Field(
        ..., ge=0.0, le=1.0, description="Precision & recall score of tool choices [0.0, 1.0]"
    )
    tool_arguments_score: float = Field(
        ..., ge=0.0, le=1.0, description="Validity and correctness of tool arguments [0.0, 1.0]"
    )
    tool_sequence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Adherence to logical tool execution order [0.0, 1.0]"
    )
    task_completion_score: float = Field(
        ..., ge=0.0, le=1.0, description="Goal and task achievement score [0.0, 1.0]"
    )
    efficiency_score: float = Field(
        ..., ge=0.0, le=1.0, description="Efficiency score penalized for redundant steps"
    )
    unnecessary_steps_count: int = Field(
        ..., ge=0, description="Count of redundant or unnecessary tool calls"
    )
    overall_score: float = Field(
        ..., ge=0.0, le=1.0, description="Weighted composite agent evaluation score"
    )
    passed: bool = Field(..., description="Whether trajectory meets passing thresholds")
    diagnostic_reasons: list[str] = Field(
        default_factory=list, description="Detailed diagnostic evaluation feedback"
    )
