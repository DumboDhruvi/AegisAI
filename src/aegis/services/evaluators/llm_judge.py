"""LLM-as-a-Judge evaluators for semantic reasoning and deep metric evaluation."""

from __future__ import annotations

import json
import re
from typing import Any

from aegis.domain.models.evaluation import EvaluationInput, MetricResult, MetricType
from aegis.infrastructure.llm import LlmProvider
from aegis.services.evaluators.base import Evaluator


def _extract_json_payload(raw_text: str) -> dict[str, Any] | None:
    """Safely extract a JSON object from text, even if wrapped in markdown fences."""
    text = raw_text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    else:
        brace_match = re.search(r"\{.*?\}", text, re.DOTALL)
        if brace_match:
            text = brace_match.group(0)

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


class BaseLlmJudge(Evaluator):
    """Base class for LLM-assisted judge evaluators."""

    def __init__(
        self,
        llm_provider: LlmProvider,
        default_threshold: float = 0.7,
    ) -> None:
        self._llm = llm_provider
        self._default_threshold = default_threshold

    @property
    def default_threshold(self) -> float:
        return self._default_threshold

    def _parse_llm_response(
        self,
        raw_output: str,
        threshold: float,
        metric_type: MetricType,
    ) -> MetricResult:
        """Parse raw LLM output into a validated MetricResult."""
        payload = _extract_json_payload(raw_output)

        if payload and "score" in payload:
            try:
                score_raw = float(payload["score"])
                score = max(0.0, min(1.0, round(score_raw, 4)))
                passed = payload.get("passed", score >= threshold)
                reason = str(payload.get("reason", "Evaluation completed by LLM judge."))
                return MetricResult(
                    metric_type=metric_type,
                    score=score,
                    passed=bool(passed),
                    threshold=threshold,
                    reason=reason,
                    details={"raw_judge_output": raw_output},
                )
            except (ValueError, TypeError):
                pass

        # Fallback heuristic if JSON structure was omitted
        score_match = re.search(
            r"\b(?:score|rating):\s*([0-1](?:\.\d+)?)\b", raw_output, re.IGNORECASE
        )
        if score_match:
            score = round(float(score_match.group(1)), 4)
            passed = score >= threshold
            return MetricResult(
                metric_type=metric_type,
                score=score,
                passed=passed,
                threshold=threshold,
                reason=raw_output.strip(),
                details={"parsed_fallback": True},
            )

        # Default fallback if parsing fails completely
        return MetricResult(
            metric_type=metric_type,
            score=0.5,
            passed=False,
            threshold=threshold,
            reason=f"Judge produced non-standard output: {raw_output[:200]}",
            details={"parse_error": True, "raw_judge_output": raw_output},
        )


class LlmFaithfulnessJudge(BaseLlmJudge):
    """Evaluates whether all factual claims in the answer are grounded in the retrieved context."""

    @property
    def metric_type(self) -> MetricType:
        return MetricType.FAITHFULNESS

    async def evaluate(
        self,
        input_data: EvaluationInput,
        threshold: float | None = None,
    ) -> MetricResult:
        thresh = threshold if threshold is not None else self._default_threshold

        if not input_data.retrieved_context:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                passed=False,
                threshold=thresh,
                reason="No retrieved context was provided; cannot assess faithfulness.",
                details={"error": "missing_context"},
            )

        prompt = (
            "You are an expert AI evaluator assessing FAITHFULNESS (groundedness).\n"
            "Task: Check if EVERY factual statement made in the ACTUAL ANSWER is directly "
            "supported by the RETRIEVED CONTEXT. If ungrounded facts exist, penalize score.\n\n"
            f"QUESTION: {input_data.question}\n"
            f"ACTUAL ANSWER: {input_data.actual_answer}\n\n"
            "Output format (JSON ONLY):\n"
            '{"score": <0.0 to 1.0>, "passed": <true/false>, "reason": "<explanation>"}'
        )

        raw_output = self._llm.generate(prompt=prompt, context=input_data.retrieved_context)
        return self._parse_llm_response(raw_output, thresh, self.metric_type)


class LlmCorrectnessJudge(BaseLlmJudge):
    """Evaluates factual and semantic alignment between answer and expected ground truth."""

    @property
    def metric_type(self) -> MetricType:
        return MetricType.CORRECTNESS

    async def evaluate(
        self,
        input_data: EvaluationInput,
        threshold: float | None = None,
    ) -> MetricResult:
        thresh = threshold if threshold is not None else self._default_threshold

        if not input_data.expected_answer or not input_data.expected_answer.strip():
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                passed=False,
                threshold=thresh,
                reason="Expected answer (ground truth) is required to evaluate correctness.",
                details={"error": "missing_expected_answer"},
            )

        prompt = (
            "You are an expert AI evaluator assessing CORRECTNESS.\n"
            "Task: Compare the ACTUAL ANSWER against the EXPECTED ANSWER (ground truth). "
            "Evaluate whether the factual meaning and conclusions align.\n\n"
            f"QUESTION: {input_data.question}\n"
            f"EXPECTED ANSWER: {input_data.expected_answer}\n"
            f"ACTUAL ANSWER: {input_data.actual_answer}\n\n"
            "Output format (JSON ONLY):\n"
            '{"score": <0.0 to 1.0>, "passed": <true/false>, "reason": "<explanation>"}'
        )

        raw_output = self._llm.generate(prompt=prompt, context=input_data.retrieved_context)
        return self._parse_llm_response(raw_output, thresh, self.metric_type)


class LlmAnswerRelevanceJudge(BaseLlmJudge):
    """Evaluates whether the actual answer directly and effectively addresses the question."""

    @property
    def metric_type(self) -> MetricType:
        return MetricType.ANSWER_RELEVANCE

    async def evaluate(
        self,
        input_data: EvaluationInput,
        threshold: float | None = None,
    ) -> MetricResult:
        thresh = threshold if threshold is not None else self._default_threshold

        prompt = (
            "You are an expert AI evaluator assessing ANSWER RELEVANCE.\n"
            "Task: Determine if the ACTUAL ANSWER directly addresses the user QUESTION "
            "without digressing, dodging, or adding superfluous unrelated content.\n\n"
            f"QUESTION: {input_data.question}\n"
            f"ACTUAL ANSWER: {input_data.actual_answer}\n\n"
            "Output format (JSON ONLY):\n"
            '{"score": <0.0 to 1.0>, "passed": <true/false>, "reason": "<explanation>"}'
        )

        raw_output = self._llm.generate(prompt=prompt, context=[])
        return self._parse_llm_response(raw_output, thresh, self.metric_type)
