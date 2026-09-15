"""Robustness evaluation orchestrator comparing baseline vs perturbed inputs (Module 6)."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from aegis.domain.models.evaluation import EvaluationInput
from aegis.domain.models.robustness import (
    PerturbationComparison,
    PerturbationType,
    RobustnessReport,
    RobustnessTestCase,
)
from aegis.services.evaluation_engine import EvaluationEngine
from aegis.services.perturbation_engine import PerturbationEngine

logger = logging.getLogger(__name__)


class RobustnessTester:
    """Evaluates comparative performance deltas across synthetic and adversarial perturbations."""

    def __init__(
        self,
        evaluation_engine: EvaluationEngine | None = None,
        perturbation_engine: PerturbationEngine | None = None,
        max_allowed_degradation: float = 0.25,
    ) -> None:
        self._eval_engine = evaluation_engine or EvaluationEngine()
        self._perturb_engine = perturbation_engine or PerturbationEngine()
        self._max_allowed_degradation = max_allowed_degradation

    async def evaluate_test_case(
        self,
        test_case: RobustnessTestCase,
        max_degradation: float | None = None,
    ) -> PerturbationComparison:
        """Run paired baseline and perturbed evaluation and compute quality degradation."""
        threshold = self._max_allowed_degradation if max_degradation is None else max_degradation

        # Run baseline evaluation
        baseline_res = await self._eval_engine.evaluate_case(test_case.baseline_input)
        baseline_score = baseline_res.composite_score

        # Run perturbed evaluation
        perturbed_res = await self._eval_engine.evaluate_case(test_case.perturbed_input)
        perturbed_score = perturbed_res.composite_score

        score_delta = round(perturbed_score - baseline_score, 4)

        if baseline_score > 0.0:
            degradation = max(0.0, baseline_score - perturbed_score) / baseline_score
        else:
            degradation = 0.0 if perturbed_score >= baseline_score else 1.0

        degradation_ratio = round(degradation, 4)
        passed = degradation_ratio <= threshold

        if passed:
            reason = (
                f"PASSED: Score delta {score_delta:+.3f} (degradation {degradation_ratio:.1%}) "
                f"within allowable degradation limit {threshold:.1%}."
            )
        else:
            reason = (
                f"FAILED: Severe performance drop {score_delta:+.3f} "
                f"({degradation_ratio:.1%} degradation exceeds allowed {threshold:.1%})."
            )

        return PerturbationComparison(
            test_case_id=test_case.id,
            perturbation_type=test_case.perturbation_type,
            baseline_score=baseline_score,
            perturbed_score=perturbed_score,
            score_delta=score_delta,
            degradation_ratio=degradation_ratio,
            robustness_passed=passed,
            reason=reason,
        )

    async def evaluate_suite(
        self,
        baseline_inputs: Sequence[EvaluationInput],
        perturbation_types: Sequence[PerturbationType] | None = None,
        max_degradation: float | None = None,
    ) -> RobustnessReport:
        """Generate perturbations and run a full comparative robustness evaluation suite."""
        effective_types = (
            list(perturbation_types)
            if perturbation_types is not None
            else [
                PerturbationType.TYPOS,
                PerturbationType.AMBIGUITY,
                PerturbationType.MISSING_INFO,
                PerturbationType.CONFLICTING_DOCS,
                PerturbationType.IRRELEVANT_DOCS,
                PerturbationType.PROMPT_INJECTION,
                PerturbationType.OUT_OF_DOMAIN,
            ]
        )

        threshold = self._max_allowed_degradation if max_degradation is None else max_degradation

        comparisons: list[PerturbationComparison] = []

        for idx, b_input in enumerate(baseline_inputs, start=1):
            for p_type in effective_types:
                case = self._perturb_engine.create_robustness_test_case(
                    baseline_input=b_input,
                    perturbation_type=p_type,
                    case_id=f"rob-case-{idx}-{p_type.value}",
                )
                comp = await self.evaluate_test_case(case, max_degradation=threshold)
                comparisons.append(comp)

        return self._aggregate_report(comparisons)

    def _aggregate_report(self, comparisons: list[PerturbationComparison]) -> RobustnessReport:
        """Aggregate individual comparisons into a comprehensive RobustnessReport."""
        total = len(comparisons)
        if total == 0:
            return RobustnessReport(
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                average_baseline_score=1.0,
                average_perturbed_score=1.0,
                overall_degradation=0.0,
                robustness_score=1.0,
                breakdown_by_type={},
                comparisons=[],
                passed=True,
                summary="No comparative robustness tests executed.",
            )

        passed_count = sum(1 for c in comparisons if c.robustness_passed)
        failed_count = total - passed_count

        avg_baseline = round(sum(c.baseline_score for c in comparisons) / total, 4)
        avg_perturbed = round(sum(c.perturbed_score for c in comparisons) / total, 4)
        overall_deg = round(max(0.0, avg_baseline - avg_perturbed), 4)
        robustness_score = round(max(0.0, 1.0 - overall_deg), 4)

        # Breakdown by perturbation type
        breakdown: dict[str, float] = {}
        by_type: dict[str, list[float]] = {}
        for c in comparisons:
            by_type.setdefault(c.perturbation_type.value, []).append(c.degradation_ratio)

        for p_type_str, deg_list in by_type.items():
            breakdown[p_type_str] = round(sum(deg_list) / len(deg_list), 4)

        all_passed = failed_count == 0

        summary = (
            f"Robustness Score: {robustness_score:.2f} | "
            f"Passed: {passed_count}/{total} tests ({passed_count / total:.1%}) | "
            f"Average baseline: {avg_baseline:.3f} -> perturbed: {avg_perturbed:.3f} "
            f"(overall degradation: {overall_deg:.3f})."
        )

        return RobustnessReport(
            total_tests=total,
            passed_tests=passed_count,
            failed_tests=failed_count,
            average_baseline_score=avg_baseline,
            average_perturbed_score=avg_perturbed,
            overall_degradation=overall_deg,
            robustness_score=robustness_score,
            breakdown_by_type=breakdown,
            comparisons=comparisons,
            passed=all_passed,
            summary=summary,
        )
