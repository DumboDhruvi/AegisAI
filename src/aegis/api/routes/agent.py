"""FastAPI routes for Agent Evaluation (Module 7)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from aegis.domain.models.agent import (
    AgentEvaluationResult,
    AgentTrajectory,
    ToolCall,
)
from aegis.services.agent_evaluator import (
    AgentTrajectoryEvaluator,
    MockAgentToolRegistry,
)

router = APIRouter(prefix="/agent", tags=["Agent Evaluation"])

_evaluator = AgentTrajectoryEvaluator()


class SimulateToolStep(BaseModel):
    """Specification of a tool to execute during simulation."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Tool name to invoke")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Arguments to pass to the tool"
    )


class SimulateAgentRequest(BaseModel):
    """Request payload to simulate tool executions and evaluate the resulting trajectory."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(..., min_length=1, description="Agent goal or instruction")
    steps: list[SimulateToolStep] = Field(
        ..., min_length=1, description="Sequence of tool calls to simulate"
    )
    final_answer: str | None = Field(
        default=None, description="Final answer generated after tool execution"
    )
    expected_tools: list[str] | None = Field(
        default=None, description="Expected tools to be selected"
    )
    expected_sequence: list[str] | None = Field(
        default=None, description="Expected exact order of tools"
    )


@router.post(
    "/evaluate-trajectory",
    response_model=AgentEvaluationResult,
    status_code=status.HTTP_200_OK,
    summary="Evaluate agent trajectory",
    description=(
        "Evaluates tool selection, arguments, sequence order, efficiency, and task completion."
    ),
)
async def evaluate_agent_trajectory(trajectory: AgentTrajectory) -> AgentEvaluationResult:
    """Evaluate an agent's multi-step execution trajectory."""
    try:
        return _evaluator.evaluate_trajectory(trajectory)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent trajectory evaluation failed: {e}",
        ) from e


@router.post(
    "/simulate-and-evaluate",
    response_model=AgentEvaluationResult,
    status_code=status.HTTP_200_OK,
    summary="Simulate and evaluate agent execution",
    description="Executes tools against mock registry and evaluates the resulting trajectory.",
)
async def simulate_and_evaluate(payload: SimulateAgentRequest) -> AgentEvaluationResult:
    """Simulate tool executions and evaluate the resulting agent trajectory."""
    try:
        executed_steps: list[ToolCall] = []
        for step in payload.steps:
            output = MockAgentToolRegistry.execute(step.name, step.arguments)
            executed_steps.append(
                ToolCall(
                    name=step.name,
                    arguments=step.arguments,
                    output=output,
                )
            )

        trajectory = AgentTrajectory(
            task=payload.task,
            steps=executed_steps,
            final_answer=payload.final_answer,
            expected_tools=payload.expected_tools,
            expected_sequence=payload.expected_sequence,
        )

        return _evaluator.evaluate_trajectory(trajectory)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent simulation and evaluation failed: {e}",
        ) from e
