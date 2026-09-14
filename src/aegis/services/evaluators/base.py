"""Base protocol and interfaces for evaluators."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from aegis.domain.models.evaluation import EvaluationInput, MetricResult, MetricType


@runtime_checkable
class Evaluator(Protocol):
    """Protocol defining the interface for all evaluation metric calculators."""

    @property
    def metric_type(self) -> MetricType:
        """The evaluation metric type evaluated by this component."""
        ...

    @property
    def default_threshold(self) -> float:
        """The default passing threshold for this metric (0.0 to 1.0)."""
        ...

    async def evaluate(
        self,
        input_data: EvaluationInput,
        threshold: float | None = None,
    ) -> MetricResult:
        """Evaluate input data and return a structured MetricResult."""
        ...
