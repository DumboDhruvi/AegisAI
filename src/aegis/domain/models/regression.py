"""Domain models for Baseline diffing and Regression Testing (Module 9)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RegressionStatus(str, Enum):
    """Classification of a metric difference compared to baseline."""

    IMPROVEMENT = "IMPROVEMENT"
    STABLE = "STABLE"
    REGRESSION = "REGRESSION"


class BaselineRecord(BaseModel):
    """A persisted reference baseline snapshot for evaluation metrics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    baseline_id: str = Field(..., min_length=1, description="Unique baseline identifier")
    dataset_version: str = Field(..., description="Version tag of dataset used for baseline")
    model_id: str = Field(..., description="Target model ID evaluated for baseline")
    metrics: dict[str, float] = Field(
        ..., description="Dictionary of metric names mapped to baseline scores in [0.0, 1.0]"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when baseline was recorded",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary run metadata and environment info"
    )


class RegressionComparison(BaseModel):
    """Granular comparison of a single metric between current run and baseline."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_name: str = Field(..., description="Name of the evaluated metric")
    baseline_score: float = Field(
        ..., ge=0.0, le=1.0, description="Reference score recorded in baseline"
    )
    current_score: float = Field(
        ..., ge=0.0, le=1.0, description="Observed score in the current evaluation run"
    )
    delta: float = Field(..., description="Score change (current_score - baseline_score)")
    max_allowed_drop: float = Field(
        default=0.05, ge=0.0, le=1.0, description="Permissible regression tolerance margin"
    )
    status: RegressionStatus = Field(..., description="IMPROVEMENT, STABLE, or REGRESSION")
    passed: bool = Field(..., description="True if no unacceptable regression occurred")
    diagnostic: str = Field(..., description="Detailed explanation of comparison result")


class RegressionReport(BaseModel):
    """Composite regression report comparing all current evaluation metrics against baseline."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    baseline_id: str = Field(..., description="Reference baseline ID")
    current_version: str = Field(..., description="Version or release tag of current system")
    has_regression: bool = Field(..., description="True if one or more metrics regressed")
    passed: bool = Field(..., description="Quality gate pass/fail flag (false if regressed)")
    comparisons: list[RegressionComparison] = Field(..., description="Per-metric comparison diffs")
    summary: str = Field(..., description="Executive diagnostic summary of regression diff")
