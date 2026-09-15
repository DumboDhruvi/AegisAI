"""Domain models for Observability, Distributed Tracing, and Diagnostics (Module 12)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from aegis.domain.models.agent import ToolCall
from aegis.domain.models.rag import RetrievedDocument


class SpanType(str, Enum):
    """Execution step classification for distributed tracing."""

    REQUEST = "REQUEST"
    RETRIEVAL = "RETRIEVAL"
    TOOL_CALL = "TOOL_CALL"
    LLM_INFERENCE = "LLM_INFERENCE"
    EVALUATION = "EVALUATION"


class TraceSpan(BaseModel):
    """Granular execution span within an evaluation trace."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    span_id: str = Field(..., description="Unique span identifier")
    name: str = Field(..., description="Span operation name")
    span_type: SpanType = Field(..., description="Categorical span type")
    start_time: datetime = Field(..., description="Span start timestamp")
    end_time: datetime = Field(..., description="Span end timestamp")
    duration_ms: float = Field(..., ge=0.0, description="Calculated duration in milliseconds")
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary span attributes and parameters"
    )
    error: str | None = Field(default=None, description="Error message if span faulted")


class EvaluationTraceRecord(BaseModel):
    """Comprehensive observability record capturing the entire execution lifecycle.

    Records:
    - Request: run_id, request_id, timestamp
    - Model: model_name
    - Prompt: prompt
    - Retrieved documents: retrieved_documents
    - Tool calls: tool_calls
    - Latency: latency_ms
    - Tokens: tokens
    - Cost: cost_usd
    - Answer: answer
    - Evaluation: evaluation_results, passed
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str = Field(..., description="Unique evaluation execution run identifier")
    request_id: str = Field(..., description="Originating client or workflow request identifier")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the execution",
    )
    model_name: str = Field(..., description="Underlying LLM identifier")
    prompt: str = Field(..., description="Full input prompt or user question")
    retrieved_documents: list[RetrievedDocument] = Field(
        default_factory=list, description="Documents retrieved during context retrieval"
    )
    tool_calls: list[ToolCall] = Field(
        default_factory=list, description="Tool invocations executed during run"
    )
    latency_ms: dict[str, float] = Field(
        default_factory=dict,
        description="Latency breakdown (e.g. retrieval, inference, evaluation, total)",
    )
    tokens: dict[str, int] = Field(
        default_factory=dict,
        description="Token consumption breakdown (prompt, completion, total)",
    )
    cost_usd: float = Field(
        default=0.0, ge=0.0, description="Computed inference financial cost in USD"
    )
    answer: str = Field(..., description="Generated answer text")
    evaluation_results: dict[str, float] = Field(
        default_factory=dict, description="Evaluated quality metrics (faithfulness, etc.)"
    )
    passed: bool = Field(default=True, description="True if evaluation passed all quality gates")
    spans: list[TraceSpan] = Field(default_factory=list, description="Fine-grained execution spans")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary execution context and tags"
    )


class TraceFilter(BaseModel):
    """Query filter parameters for retrieving evaluation traces."""

    model_config = ConfigDict(extra="forbid")

    model_name: str | None = Field(default=None, description="Filter by LLM name")
    passed: bool | None = Field(
        default=None, description="Filter by pass/fail status (set False for diagnostics)"
    )
    min_cost_usd: float | None = Field(default=None, ge=0.0, description="Min cost threshold")
    min_latency_ms: float | None = Field(default=None, ge=0.0, description="Min latency threshold")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum traces to return")


class TraceSummary(BaseModel):
    """Aggregated operational metrics across recorded evaluation traces."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_traces: int = Field(..., ge=0, description="Total traces recorded")
    failed_traces: int = Field(..., ge=0, description="Count of failed evaluations")
    failure_rate: float = Field(..., ge=0.0, le=1.0, description="Ratio of failed evaluations")
    mean_latency_ms: float = Field(..., ge=0.0, description="Average total latency in ms")
    total_tokens: int = Field(..., ge=0, description="Total tokens consumed across all runs")
    total_cost_usd: float = Field(..., ge=0.0, description="Total financial spend in USD")
