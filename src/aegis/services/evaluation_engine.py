"""Core evaluation engine orchestrating metrics, concurrency, and score aggregation."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Any

from aegis.domain.models.evaluation import (
    EvaluationInput,
    EvaluationResult,
    MetricResult,
    MetricType,
)
from aegis.services.evaluators.base import Evaluator
from aegis.services.evaluators.deterministic import (
    F1CorrectnessEvaluator,
    KeywordRelevanceEvaluator,
    LexicalFaithfulnessEvaluator,
)


class EvaluationEngine:
    """Orchestrates multi-metric evaluation runs, threshold enforcement, and result aggregation."""

    def __init__(
        self,
        evaluators: Sequence[Evaluator] | None = None,
        weights: dict[MetricType, float] | None = None,
    ) -> None:
        """Initialize the engine with evaluators and optional metric weighting.

        If no evaluators are provided, the default deterministic suite is used:
        - LexicalFaithfulnessEvaluator (Faithfulness)
        - F1CorrectnessEvaluator (Correctness)
        - KeywordRelevanceEvaluator (Answer Relevance)
        """
        if evaluators is not None:
            self._evaluators: list[Evaluator] = list(evaluators)
        else:
            self._evaluators = [
                LexicalFaithfulnessEvaluator(),
                F1CorrectnessEvaluator(),
                KeywordRelevanceEvaluator(),
            ]

        self._weights: dict[MetricType, float] = weights or {}

    @property
    def evaluators(self) -> list[Evaluator]:
        """List of active evaluators configured in the engine."""
        return list(self._evaluators)

    def add_evaluator(self, evaluator: Evaluator) -> None:
        """Register an additional evaluator in the engine."""
        self._evaluators.append(evaluator)

    async def evaluate_case(
        self,
        input_data: EvaluationInput,
        thresholds: dict[MetricType, float] | None = None,
    ) -> EvaluationResult:
        """Evaluate a single test case across all configured evaluators concurrently."""
        threshold_map = thresholds or {}

        tasks = [
            evaluator.evaluate(
                input_data,
                threshold=threshold_map.get(evaluator.metric_type),
            )
            for evaluator in self._evaluators
        ]

        metric_results: list[MetricResult] = await asyncio.gather(*tasks)

        if not metric_results:
            raise ValueError("No evaluators configured in EvaluationEngine.")

        # Compute composite score
        total_weight = 0.0
        weighted_sum = 0.0

        for res in metric_results:
            weight = self._weights.get(res.metric_type, 1.0)
            weighted_sum += res.score * weight
            total_weight += weight

        composite_score = round(weighted_sum / total_weight, 4) if total_weight > 0 else 0.0
        all_passed = all(res.passed for res in metric_results)

        return EvaluationResult(
            case_id=input_data.case_id,
            question=input_data.question,
            actual_answer=input_data.actual_answer,
            passed=all_passed,
            composite_score=composite_score,
            metrics=metric_results,
        )

    async def evaluate_batch(
        self,
        cases: Sequence[EvaluationInput],
        thresholds: dict[MetricType, float] | None = None,
    ) -> list[EvaluationResult]:
        """Evaluate multiple test cases concurrently."""
        tasks = [self.evaluate_case(case, thresholds=thresholds) for case in cases]
        return list(await asyncio.gather(*tasks))

    def describe_metrics(self) -> list[dict[str, Any]]:
        """Return human-readable metadata describing all active metrics in the engine."""
        return [
            {
                "metric_type": ev.metric_type.value,
                "default_threshold": ev.default_threshold,
                "evaluator_class": ev.__class__.__name__,
            }
            for ev in self._evaluators
        ]
