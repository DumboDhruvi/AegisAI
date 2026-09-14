"""Deterministic evaluators for fast, zero-cost, reproducible offline testing."""

from __future__ import annotations

import re
import string
from collections import Counter

from aegis.domain.models.evaluation import EvaluationInput, MetricResult, MetricType
from aegis.services.evaluators.base import Evaluator


def _normalize_text(text: str) -> str:
    """Lowercase text and remove punctuation and excess whitespace."""
    text = text.lower()
    text = "".join(ch for ch in text if ch not in string.punctuation)
    return " ".join(text.split())


def _tokenize(text: str) -> list[str]:
    """Tokenize normalized text into words."""
    norm = _normalize_text(text)
    return norm.split() if norm else []


# Standard lightweight English stopwords for relevance scoring
_STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "because",
    "as",
    "what",
    "which",
    "this",
    "that",
    "these",
    "those",
    "then",
    "just",
    "so",
    "than",
    "such",
    "both",
    "through",
    "about",
    "for",
    "is",
    "of",
    "while",
    "during",
    "to",
    "from",
    "in",
    "out",
    "on",
    "off",
    "again",
    "further",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "any",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "too",
    "very",
    "can",
    "will",
    "should",
    "now",
    "are",
    "was",
    "were",
    "been",
    "being",
    "have",
    "has",
    "had",
    "having",
    "do",
    "does",
    "did",
    "doing",
    "would",
}


class F1CorrectnessEvaluator(Evaluator):
    """Calculates token-level F1 score between actual_answer and expected_answer."""

    def __init__(self, default_threshold: float = 0.7) -> None:
        self._default_threshold = default_threshold

    @property
    def metric_type(self) -> MetricType:
        return MetricType.CORRECTNESS

    @property
    def default_threshold(self) -> float:
        return self._default_threshold

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
                reason="Expected answer (ground truth) is missing; cannot evaluate correctness.",
                details={"error": "missing_expected_answer"},
            )

        pred_tokens = _tokenize(input_data.actual_answer)
        gold_tokens = _tokenize(input_data.expected_answer)

        if not pred_tokens and not gold_tokens:
            return MetricResult(
                metric_type=self.metric_type,
                score=1.0,
                passed=True,
                threshold=thresh,
                reason="Both actual and expected answers are empty tokens.",
                details={"precision": 1.0, "recall": 1.0, "f1": 1.0},
            )

        if not pred_tokens or not gold_tokens:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                passed=False,
                threshold=thresh,
                reason="One of actual or expected answers contains no non-punctuation tokens.",
                details={"precision": 0.0, "recall": 0.0, "f1": 0.0},
            )

        pred_counter = Counter(pred_tokens)
        gold_counter = Counter(gold_tokens)
        common = pred_counter & gold_counter
        num_same = sum(common.values())

        if num_same == 0:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                passed=False,
                threshold=thresh,
                reason="No common tokens found between actual answer and expected answer.",
                details={"precision": 0.0, "recall": 0.0, "f1": 0.0, "overlap_count": 0},
            )

        precision = num_same / len(pred_tokens)
        recall = num_same / len(gold_tokens)
        f1 = (2 * precision * recall) / (precision + recall)
        score = round(f1, 4)
        passed = score >= thresh

        reason = (
            f"F1 correctness score of {score:.4f} "
            f"(Precision: {precision:.2f}, Recall: {recall:.2f}). "
            f"Found {num_same} overlapping tokens."
        )
        if not passed:
            reason += f" Did not meet required threshold of {thresh}."

        return MetricResult(
            metric_type=self.metric_type,
            score=score,
            passed=passed,
            threshold=thresh,
            reason=reason,
            details={
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": score,
                "overlap_tokens": num_same,
                "predicted_tokens": len(pred_tokens),
                "gold_tokens": len(gold_tokens),
            },
        )


class LexicalFaithfulnessEvaluator(Evaluator):
    """Evaluates grounding by checking if claims in the answer appear in retrieved context."""

    def __init__(
        self,
        default_threshold: float = 0.7,
        sentence_overlap_threshold: float = 0.5,
    ) -> None:
        self._default_threshold = default_threshold
        self._sentence_overlap_threshold = sentence_overlap_threshold

    @property
    def metric_type(self) -> MetricType:
        return MetricType.FAITHFULNESS

    @property
    def default_threshold(self) -> float:
        return self._default_threshold

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
                reason="No retrieved context provided; answer cannot be verified as faithful.",
                details={"ungrounded_sentences": [input_data.actual_answer]},
            )

        # Split answer into sentences
        sentences = [
            s.strip()
            for s in re.split(r"[.!?\n]+", input_data.actual_answer)
            if len(_tokenize(s)) >= 2
        ]

        if not sentences:
            # Answer is very short or punctuation only
            sentences = [input_data.actual_answer.strip()]

        context_full = " ".join(input_data.retrieved_context)
        context_tokens = set(_tokenize(context_full))

        grounded_count = 0
        ungrounded_sentences: list[str] = []

        for sentence in sentences:
            s_tokens = [t for t in _tokenize(sentence) if t not in _STOPWORDS]
            if not s_tokens:
                # If only stopwords, consider grounded
                grounded_count += 1
                continue

            matches = sum(1 for t in s_tokens if t in context_tokens)
            overlap_ratio = matches / len(s_tokens)

            if overlap_ratio >= self._sentence_overlap_threshold:
                grounded_count += 1
            else:
                ungrounded_sentences.append(sentence)

        score = round(grounded_count / len(sentences), 4)
        passed = score >= thresh

        if passed:
            reason = (
                f"Answer is faithful ({score:.1%}): {grounded_count} of {len(sentences)} "
                f"statements grounded in retrieved context."
            )
        else:
            reason = (
                f"Faithfulness score {score:.1%} below threshold {thresh}. "
                f"Found {len(ungrounded_sentences)} ungrounded statement(s)."
            )

        return MetricResult(
            metric_type=self.metric_type,
            score=score,
            passed=passed,
            threshold=thresh,
            reason=reason,
            details={
                "total_sentences": len(sentences),
                "grounded_sentences": grounded_count,
                "ungrounded_sentences": ungrounded_sentences,
            },
        )


class KeywordRelevanceEvaluator(Evaluator):
    """Measures how well the answer addresses key concepts and terms in the user question."""

    def __init__(self, default_threshold: float = 0.6) -> None:
        self._default_threshold = default_threshold

    @property
    def metric_type(self) -> MetricType:
        return MetricType.ANSWER_RELEVANCE

    @property
    def default_threshold(self) -> float:
        return self._default_threshold

    async def evaluate(
        self,
        input_data: EvaluationInput,
        threshold: float | None = None,
    ) -> MetricResult:
        thresh = threshold if threshold is not None else self._default_threshold

        q_tokens = [t for t in _tokenize(input_data.question) if t not in _STOPWORDS]
        if not q_tokens:
            # Question has only stopwords or punctuation, fall back to all tokens
            q_tokens = _tokenize(input_data.question)

        if not q_tokens:
            return MetricResult(
                metric_type=self.metric_type,
                score=1.0,
                passed=True,
                threshold=thresh,
                reason="Question contains no distinct keywords.",
                details={"matched_keywords": [], "missing_keywords": []},
            )

        ans_tokens = set(_tokenize(input_data.actual_answer))
        matched: list[str] = []
        missing: list[str] = []

        for kw in set(q_tokens):
            if kw in ans_tokens:
                matched.append(kw)
            else:
                missing.append(kw)

        coverage = len(matched) / (len(matched) + len(missing))
        score = round(coverage, 4)
        passed = score >= thresh

        reason = (
            f"Answer relevance score {score:.1%}. Addressed {len(matched)} of "
            f"{len(matched) + len(missing)} question keywords."
        )
        if not passed:
            reason += f" Missing key concepts: {', '.join(missing[:5])}."

        return MetricResult(
            metric_type=self.metric_type,
            score=score,
            passed=passed,
            threshold=thresh,
            reason=reason,
            details={
                "matched_keywords": matched,
                "missing_keywords": missing,
                "coverage_ratio": score,
            },
        )
