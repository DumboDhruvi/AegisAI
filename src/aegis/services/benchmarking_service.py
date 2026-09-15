"""Multi-Model Comparative Benchmarking service (Module 8)."""

from __future__ import annotations

import logging
import math
import time
from collections.abc import Callable, Sequence

from aegis.domain.models.benchmark import (
    BenchmarkComparisonReport,
    ModelBenchmarkSummary,
    ModelExecutionResult,
    ModelPricing,
)
from aegis.domain.models.evaluation import EvaluationInput, MetricType
from aegis.domain.models.evaluation_case import EvaluationCase
from aegis.services.evaluation_engine import EvaluationEngine
from aegis.services.hallucination_detector import HallucinationDetector

logger = logging.getLogger(__name__)

# Standard industry pricing tiers per million tokens (USD)
DEFAULT_PRICING_CATALOG: dict[str, ModelPricing] = {
    "gpt-4o": ModelPricing(
        model_id="gpt-4o", input_cost_per_million=2.50, output_cost_per_million=10.00
    ),
    "gpt-4o-mini": ModelPricing(
        model_id="gpt-4o-mini", input_cost_per_million=0.15, output_cost_per_million=0.60
    ),
    "claude-3-5-sonnet": ModelPricing(
        model_id="claude-3-5-sonnet", input_cost_per_million=3.00, output_cost_per_million=15.00
    ),
    "gemini-1.5-pro": ModelPricing(
        model_id="gemini-1.5-pro", input_cost_per_million=1.25, output_cost_per_million=5.00
    ),
    "gemini-1.5-flash": ModelPricing(
        model_id="gemini-1.5-flash", input_cost_per_million=0.075, output_cost_per_million=0.30
    ),
    "mock-model-a": ModelPricing(
        model_id="mock-model-a", input_cost_per_million=2.00, output_cost_per_million=8.00
    ),
    "mock-model-b": ModelPricing(
        model_id="mock-model-b", input_cost_per_million=0.20, output_cost_per_million=0.80
    ),
}


def estimate_tokens(text: str) -> int:
    """Heuristic approximation of token count (~4 characters per token in English)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


class BenchmarkingService:
    """Orchestrates comparative benchmarking across multiple models over identical test datasets."""

    def __init__(
        self,
        pricing_catalog: dict[str, ModelPricing] | None = None,
        evaluation_engine: EvaluationEngine | None = None,
        hallucination_detector: HallucinationDetector | None = None,
    ) -> None:
        self._pricing = pricing_catalog or dict(DEFAULT_PRICING_CATALOG)
        self._eval_engine = evaluation_engine or EvaluationEngine()
        self._hallucination_detector = hallucination_detector or HallucinationDetector()

    def get_pricing_catalog(self) -> dict[str, ModelPricing]:
        """Return registered model pricing configurations."""
        return dict(self._pricing)

    def register_pricing(self, pricing: ModelPricing) -> None:
        """Register or update custom model token pricing."""
        self._pricing[pricing.model_id] = pricing

    def calculate_cost(self, model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Compute estimated USD cost for token consumption."""
        pricing = self._pricing.get(
            model_id,
            ModelPricing(
                model_id=model_id,
                input_cost_per_million=1.0,
                output_cost_per_million=2.0,
            ),
        )
        cost = (
            (prompt_tokens * pricing.input_cost_per_million)
            + (completion_tokens * pricing.output_cost_per_million)
        ) / 1_000_000
        return round(cost, 6)

    async def run_benchmark(
        self,
        dataset_name: str,
        cases: Sequence[EvaluationCase],
        model_runners: dict[str, Callable[[str, list[str]], str]] | None = None,
        precomputed_answers: dict[str, dict[str, str]] | None = None,
    ) -> BenchmarkComparisonReport:
        """Execute identical dataset against all models and compile comparative metrics."""
        benchmark_id = f"bench-{int(time.time())}"
        model_ids = (
            list(model_runners.keys())
            if model_runners
            else (
                list(precomputed_answers.keys())
                if precomputed_answers
                else ["mock-model-a", "mock-model-b"]
            )
        )

        all_summaries: dict[str, ModelBenchmarkSummary] = {}

        for model_id in model_ids:
            exec_results: list[ModelExecutionResult] = []

            for case in cases:
                prompt_text = case.question
                context = list(case.context)

                # Determine model response
                start_time = time.perf_counter()
                if precomputed_answers and model_id in precomputed_answers:
                    answer = precomputed_answers[model_id].get(
                        case.id, case.expected_answer or "Generated model response."
                    )
                elif model_runners and model_id in model_runners:
                    answer = model_runners[model_id](prompt_text, context)
                else:
                    # Deterministic mock responses for testing
                    if model_id == "mock-model-a":
                        answer = (
                            case.expected_answer
                            or f"Comprehensive answer to {case.question} supported by context."
                        )
                    else:
                        answer = f"Brief answer to {case.question}."
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0

                prompt_tokens = estimate_tokens(prompt_text + "".join(context))
                completion_tokens = estimate_tokens(answer)
                total_tokens = prompt_tokens + completion_tokens
                cost = self.calculate_cost(model_id, prompt_tokens, completion_tokens)

                # Evaluate response quality
                eval_input = EvaluationInput(
                    question=prompt_text,
                    actual_answer=answer,
                    expected_answer=case.expected_answer,
                    retrieved_context=context,
                )
                eval_res = await self._eval_engine.evaluate_case(eval_input)

                # Accuracy, Faithfulness, Relevance extraction from metrics list
                metric_map = {m.metric_type: m.score for m in eval_res.metrics}
                acc_score = metric_map.get(MetricType.CORRECTNESS, 0.8)
                faith_score = metric_map.get(MetricType.FAITHFULNESS, 0.8)
                rel_score = metric_map.get(MetricType.ANSWER_RELEVANCE, 0.8)

                # Hallucination assessment
                ground_rep = await self._hallucination_detector.verify(
                    actual_answer=answer, retrieved_context=context
                )
                hallucination_rate = ground_rep.hallucination_rate

                exec_results.append(
                    ModelExecutionResult(
                        model_id=model_id,
                        case_id=case.id,
                        actual_answer=answer,
                        accuracy_score=acc_score,
                        faithfulness_score=faith_score,
                        relevance_score=rel_score,
                        hallucination_rate=hallucination_rate,
                        latency_ms=round(elapsed_ms, 2),
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        cost_usd=cost,
                    )
                )

            all_summaries[model_id] = self._compile_summary(model_id, exec_results)

        # Determine winner model
        winner_id, recommendations = self._select_winner_and_recommend(all_summaries)

        return BenchmarkComparisonReport(
            benchmark_id=benchmark_id,
            dataset_name=dataset_name,
            evaluated_models=model_ids,
            model_summaries=all_summaries,
            winner_model_id=winner_id,
            recommendations=recommendations,
        )

    def _compile_summary(
        self, model_id: str, results: list[ModelExecutionResult]
    ) -> ModelBenchmarkSummary:
        """Compute aggregated performance and resource metrics for a model."""
        n = len(results)
        if n == 0:
            return ModelBenchmarkSummary(
                model_id=model_id,
                total_cases=0,
                mean_accuracy=0.0,
                mean_faithfulness=0.0,
                mean_relevance=0.0,
                mean_hallucination_rate=0.0,
                mean_latency_ms=0.0,
                p95_latency_ms=0.0,
                total_tokens=0,
                total_cost_usd=0.0,
                composite_quality_score=0.0,
            )

        mean_acc = sum(r.accuracy_score for r in results) / n
        mean_faith = sum(r.faithfulness_score for r in results) / n
        mean_rel = sum(r.relevance_score for r in results) / n
        mean_halluc = sum(r.hallucination_rate for r in results) / n
        mean_lat = sum(r.latency_ms for r in results) / n

        latencies = sorted(r.latency_ms for r in results)
        p95_idx = min(n - 1, math.ceil(0.95 * n) - 1)
        p95_lat = latencies[p95_idx]

        total_toks = sum(r.total_tokens for r in results)
        total_cost = sum(r.cost_usd for r in results)

        # Composite quality: 40% acc, 30% faith, 20% relevance, 10% (1 - hallucination)
        composite = (
            (mean_acc * 0.40)
            + (mean_faith * 0.30)
            + (mean_rel * 0.20)
            + ((1.0 - mean_halluc) * 0.10)
        )

        return ModelBenchmarkSummary(
            model_id=model_id,
            total_cases=n,
            mean_accuracy=round(mean_acc, 4),
            mean_faithfulness=round(mean_faith, 4),
            mean_relevance=round(mean_rel, 4),
            mean_hallucination_rate=round(mean_halluc, 4),
            mean_latency_ms=round(mean_lat, 2),
            p95_latency_ms=round(p95_lat, 2),
            total_tokens=total_toks,
            total_cost_usd=round(total_cost, 6),
            composite_quality_score=round(composite, 4),
        )

    def _select_winner_and_recommend(
        self, summaries: dict[str, ModelBenchmarkSummary]
    ) -> tuple[str, list[str]]:
        """Select winning model and generate optimization trade-off advice."""
        if not summaries:
            return "none", ["No models evaluated."]

        # Sort by composite quality score descending
        sorted_by_quality = sorted(
            summaries.values(), key=lambda s: s.composite_quality_score, reverse=True
        )
        winner = sorted_by_quality[0]

        recommendations: list[str] = [
            f"Winner '{winner.model_id}' achieved the highest composite quality score "
            f"({winner.composite_quality_score:.3f})."
        ]

        # Check for cost-efficient alternatives
        sorted_by_cost = sorted(summaries.values(), key=lambda s: s.total_cost_usd)
        cheapest = sorted_by_cost[0]
        if cheapest.model_id != winner.model_id:
            cost_savings = (
                (winner.total_cost_usd - cheapest.total_cost_usd) / winner.total_cost_usd
                if winner.total_cost_usd > 0
                else 0.0
            )
            quality_diff = winner.composite_quality_score - cheapest.composite_quality_score
            recommendations.append(
                f"Cost-effective alternative: '{cheapest.model_id}' is {cost_savings:.1%} cheaper "
                f"with a modest quality delta of -{quality_diff:.3f}."
            )

        return winner.model_id, recommendations
