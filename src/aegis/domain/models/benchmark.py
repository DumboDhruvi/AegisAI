"""Domain models for Multi-Model Comparative Benchmarking (Module 8)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ModelPricing(BaseModel):
    """Token pricing tier for a model per million tokens."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str = Field(..., description="Unique model identifier")
    input_cost_per_million: float = Field(
        ..., ge=0.0, description="Cost in USD per 1M input / prompt tokens"
    )
    output_cost_per_million: float = Field(
        ..., ge=0.0, description="Cost in USD per 1M output / completion tokens"
    )


class ModelExecutionResult(BaseModel):
    """Performance and resource metrics for a single model evaluating an individual test case."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str = Field(..., description="Evaluated model ID")
    case_id: str = Field(..., description="Associated evaluation case ID")
    actual_answer: str = Field(..., description="Generated answer text")
    accuracy_score: float = Field(..., ge=0.0, le=1.0, description="Correctness score [0.0, 1.0]")
    faithfulness_score: float = Field(
        ..., ge=0.0, le=1.0, description="Groundedness score [0.0, 1.0]"
    )
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Answer relevance [0.0, 1.0]")
    hallucination_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Hallucination rate [0.0, 1.0]"
    )
    latency_ms: float = Field(..., ge=0.0, description="End-to-end execution latency in ms")
    prompt_tokens: int = Field(..., ge=0, description="Prompt token count")
    completion_tokens: int = Field(..., ge=0, description="Generated response token count")
    total_tokens: int = Field(..., ge=0, description="Sum of prompt and completion tokens")
    cost_usd: float = Field(..., ge=0.0, description="Total computed execution cost in USD")


class ModelBenchmarkSummary(BaseModel):
    """Aggregated benchmark performance profile for a specific model across a dataset."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str = Field(..., description="Evaluated model ID")
    total_cases: int = Field(..., ge=0, description="Number of evaluated test cases")
    mean_accuracy: float = Field(..., ge=0.0, le=1.0, description="Average accuracy score")
    mean_faithfulness: float = Field(..., ge=0.0, le=1.0, description="Average faithfulness score")
    mean_relevance: float = Field(..., ge=0.0, le=1.0, description="Average relevance score")
    mean_hallucination_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Average hallucination rate"
    )
    mean_latency_ms: float = Field(..., ge=0.0, description="Mean latency across cases in ms")
    p95_latency_ms: float = Field(..., ge=0.0, description="95th percentile latency in ms")
    total_tokens: int = Field(..., ge=0, description="Total tokens consumed across all runs")
    total_cost_usd: float = Field(..., ge=0.0, description="Total cumulative cost in USD")
    composite_quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Composite weighted quality score"
    )


class BenchmarkComparisonReport(BaseModel):
    """Comparative multi-model benchmark report with winner selection and recommendations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    benchmark_id: str = Field(..., description="Identifier for this benchmark run")
    dataset_name: str = Field(..., description="Name or identifier of benchmark dataset")
    evaluated_models: list[str] = Field(..., description="List of compared model IDs")
    model_summaries: dict[str, ModelBenchmarkSummary] = Field(
        ..., description="Per-model aggregate summaries"
    )
    winner_model_id: str = Field(
        ..., description="Recommended optimal model based on quality and cost-efficiency"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Diagnostic trade-off analysis and recommendations"
    )
