"""Rubric engine service for registering, managing, and evaluating qualitative rubrics."""

from __future__ import annotations

import json
import re
from typing import Any

from aegis.domain.models.evaluation import EvaluationInput
from aegis.domain.models.rubric import (
    DEFAULT_5_POINT_RUBRIC,
    GROUNDING_RUBRIC,
    RubricDefinition,
    RubricScoreResult,
)
from aegis.infrastructure.llm import LlmProvider


def _extract_json_payload(raw_text: str) -> dict[str, Any] | None:
    """Safely extract a JSON object from text."""
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


class RubricEngine:
    """Manages rubric registration and evaluates AI responses against discrete criteria bands."""

    def __init__(self, llm_provider: LlmProvider | None = None) -> None:
        self._llm = llm_provider
        self._rubrics: dict[str, RubricDefinition] = {}

        # Preload standard default rubrics
        self.register_rubric(DEFAULT_5_POINT_RUBRIC)
        self.register_rubric(GROUNDING_RUBRIC)

    def register_rubric(self, rubric: RubricDefinition) -> None:
        """Register a new rubric specification into the engine."""
        self._rubrics[rubric.id] = rubric

    def get_rubric(self, rubric_id: str) -> RubricDefinition | None:
        """Retrieve a registered rubric by identifier."""
        return self._rubrics.get(rubric_id)

    def list_rubrics(self) -> list[RubricDefinition]:
        """List all registered rubrics."""
        return list(self._rubrics.values())

    async def evaluate_with_rubric(
        self,
        input_data: EvaluationInput,
        rubric_id: str = "standard-5-point",
        passing_score_override: int | None = None,
    ) -> RubricScoreResult:
        """Evaluate an interaction against a specific rubric definition."""
        rubric = self.get_rubric(rubric_id)
        if not rubric:
            raise KeyError(f"Rubric '{rubric_id}' is not registered in the RubricEngine.")

        threshold = (
            passing_score_override if passing_score_override is not None else rubric.passing_score
        )

        if self._llm is not None:
            return await self._evaluate_with_llm(input_data, rubric, threshold)

        return self._evaluate_deterministic_fallback(input_data, rubric, threshold)

    async def _evaluate_with_llm(
        self,
        input_data: EvaluationInput,
        rubric: RubricDefinition,
        threshold: int,
    ) -> RubricScoreResult:
        """Score using LLM-as-a-judge with structured rubric prompt."""
        criteria_text = "\n".join(
            f"  - Score {c.score} ({c.label}): {c.description}"
            for c in sorted(rubric.criteria, key=lambda x: x.score, reverse=True)
        )

        prompt = (
            f"You are an expert AI evaluator grading an interaction using the rubric "
            f"'{rubric.name}'.\n"
            f"Description: {rubric.description}\n\n"
            f"SCORING CRITERIA:\n{criteria_text}\n\n"
            f"USER QUESTION: {input_data.question}\n"
            f"EXPECTED ANSWER (Ground Truth): {input_data.expected_answer or 'N/A'}\n"
            f"ACTUAL AI ANSWER: {input_data.actual_answer}\n\n"
            f"Assign an integer score between {rubric.min_score} and {rubric.max_score} "
            f"that best matches the criteria above.\n"
            "Output format (JSON ONLY):\n"
            '{"score": <int>, "reason": "<explanation>"}'
        )

        assert self._llm is not None
        raw_output = self._llm.generate(prompt=prompt, context=input_data.retrieved_context)
        payload = _extract_json_payload(raw_output)

        raw_score: int
        reason: str

        if payload and "score" in payload:
            try:
                raw_score = int(round(float(payload["score"])))
                raw_score = max(rubric.min_score, min(rubric.max_score, raw_score))
                reason = str(payload.get("reason", "Graded by LLM rubric judge."))
            except (ValueError, TypeError):
                raw_score = rubric.min_score
                reason = f"Invalid score format from judge: {raw_output[:100]}"
        else:
            # Fallback regex search for integer score
            match = re.search(r"\b(?:score|rating):\s*(\d+)\b", raw_output, re.IGNORECASE)
            if match:
                raw_score = max(rubric.min_score, min(rubric.max_score, int(match.group(1))))
                reason = raw_output.strip()
            else:
                raw_score = rubric.min_score
                reason = f"Judge failed to produce structured score: {raw_output[:100]}"

        return self._build_result(rubric, raw_score, threshold, reason)

    def _evaluate_deterministic_fallback(
        self,
        input_data: EvaluationInput,
        rubric: RubricDefinition,
        threshold: int,
    ) -> RubricScoreResult:
        """Deterministic heuristic fallback when no LLM is configured."""
        actual_tokens = set(input_data.actual_answer.lower().split())

        # If expected answer exists, compute overlap
        if input_data.expected_answer:
            gold_tokens = set(input_data.expected_answer.lower().split())
            overlap = len(actual_tokens & gold_tokens)
            ratio = overlap / len(gold_tokens) if gold_tokens else 0.0
            score_range = rubric.max_score - rubric.min_score
            raw_score = rubric.min_score + int(round(ratio * score_range))
            raw_score = max(rubric.min_score, min(rubric.max_score, raw_score))
            reason = (
                f"Deterministic token overlap {ratio:.1%} against expected ground truth "
                f"mapped to score {raw_score}/{rubric.max_score}."
            )
        else:
            # Check context grounding
            context_text = " ".join(input_data.retrieved_context).lower()
            context_tokens = set(context_text.split())
            if context_tokens:
                overlap = len(actual_tokens & context_tokens)
                ratio = overlap / len(actual_tokens) if actual_tokens else 0.0
                score_range = rubric.max_score - rubric.min_score
                raw_score = rubric.min_score + int(round(ratio * score_range))
                raw_score = max(rubric.min_score, min(rubric.max_score, raw_score))
                reason = (
                    f"Deterministic context overlap {ratio:.1%} mapped to "
                    f"score {raw_score}/{rubric.max_score}."
                )
            else:
                raw_score = rubric.min_score
                reason = "No ground truth or context provided; assigned minimum rubric score."

        return self._build_result(rubric, raw_score, threshold, reason)

    def _build_result(
        self,
        rubric: RubricDefinition,
        raw_score: int,
        threshold: int,
        reason: str,
    ) -> RubricScoreResult:
        """Compute normalized score, passing status, and qualitative label."""
        span = rubric.max_score - rubric.min_score
        normalized = (raw_score - rubric.min_score) / span if span > 0 else 0.0
        normalized = max(0.0, min(1.0, round(normalized, 4)))

        passed = raw_score >= threshold
        crit = rubric.get_criterion_for_score(raw_score)
        assigned_label = crit.label if crit else f"Score {raw_score}"

        return RubricScoreResult(
            rubric_id=rubric.id,
            raw_score=raw_score,
            normalized_score=normalized,
            passed=passed,
            assigned_label=assigned_label,
            reason=reason,
        )
