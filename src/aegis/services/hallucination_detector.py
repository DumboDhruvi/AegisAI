"""Hallucination detection and evidence attribution service (Module 5)."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Sequence

from aegis.domain.models.grounding import (
    ClaimStatus,
    ClaimVerification,
    EvidenceCitation,
    ExtractedClaim,
    GroundingReport,
)
from aegis.infrastructure.llm import LlmProvider

logger = logging.getLogger(__name__)

# Common conversational boilerplate to skip during claim extraction
_CONVERSATIONAL_BOILERPLATE = {
    "hello",
    "hi",
    "hey",
    "sure",
    "sure thing",
    "certainly",
    "here is the answer",
    "here is the information",
    "hope this helps",
    "let me know if you need anything else",
    "thanks",
    "thank you",
}

# Negation and contradiction indicator tokens
_NEGATION_WORDS = {
    "no",
    "not",
    "never",
    "neither",
    "nor",
    "none",
    "nobody",
    "nowhere",
    "cannot",
    "can't",
    "won't",
    "isn't",
    "aren't",
    "wasn't",
    "weren't",
}


def _tokenize(text: str) -> list[str]:
    """Lowercase tokenization removing non-alphanumeric characters."""
    return re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())


def _extract_json_payload(raw_text: str) -> dict[str, object]:
    """Extract JSON from raw LLM output, peeling markdown fences if present."""
    clean = raw_text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean)
    if match:
        clean = match.group(1).strip()

    try:
        parsed = json.loads(clean)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    curly_match = re.search(r"\{[\s\S]*\}", clean)
    if curly_match:
        try:
            parsed = json.loads(curly_match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return {}


class ClaimExtractor:
    """Extracts atomic factual claims and character spans from an answer."""

    def extract_claims(self, text: str) -> list[ExtractedClaim]:
        """Splits answer into sentences, filtering empty lines and conversational filler."""
        if not text.strip():
            return []

        # Split on sentence terminals followed by whitespace
        sentence_spans: list[tuple[str, int, int]] = []
        pattern = re.compile(r"([^.!?\n]+[.!?]*)", re.UNICODE)

        for match in pattern.finditer(text):
            sentence = match.group(1).strip()
            if not sentence:
                continue

            # Strip non-alphanumeric markers like markdown bullets
            cleaned = re.sub(r"^[-*#\d.]+\s*", "", sentence).strip()
            if not cleaned:
                continue

            # Filter trivial conversational phrases
            if cleaned.lower().rstrip(".!?:") in _CONVERSATIONAL_BOILERPLATE:
                continue

            # Skip sentences with fewer than 3 words (rarely contain standalone factual claims)
            words = _tokenize(cleaned)
            if len(words) < 3:
                continue

            sentence_spans.append((cleaned, match.start(), match.end()))

        # Fallback if no sentence boundaries matched but text has content
        if not sentence_spans and len(_tokenize(text)) >= 3:
            sentence_spans.append((text.strip(), 0, len(text)))

        claims: list[ExtractedClaim] = []
        for idx, (claim_text, start, end) in enumerate(sentence_spans, start=1):
            claims.append(
                ExtractedClaim(
                    claim_id=f"claim-{idx}",
                    claim_text=claim_text,
                    start_char=start,
                    end_char=end,
                )
            )

        return claims


class HallucinationDetector:
    """Detects unsupported, supported, or contradictory claims against context."""

    def __init__(
        self,
        llm_provider: LlmProvider | None = None,
        claim_extractor: ClaimExtractor | None = None,
        default_threshold: float = 0.8,
    ) -> None:
        self._llm = llm_provider
        self._extractor = claim_extractor or ClaimExtractor()
        self._threshold = default_threshold

    def extract_claims(self, text: str) -> list[ExtractedClaim]:
        """Public helper to extract atomic claims from a response."""
        return self._extractor.extract_claims(text)

    async def verify(
        self,
        actual_answer: str,
        retrieved_context: Sequence[str],
        threshold: float | None = None,
        question: str | None = None,
    ) -> GroundingReport:
        """Verify grounding of each claim in actual_answer against retrieved_context."""
        effective_threshold = self._threshold if threshold is None else threshold
        claims = self._extractor.extract_claims(actual_answer)

        if not claims:
            return GroundingReport(
                total_claims=0,
                supported_claims=0,
                unsupported_claims=0,
                contradictory_claims=0,
                grounding_ratio=1.0,
                hallucination_rate=0.0,
                passed=True,
                claims=[],
                summary="No factual claims identified in response to verify.",
            )

        if not retrieved_context or all(not c.strip() for c in retrieved_context):
            # No context provided — all claims are ungrounded
            verifications = [
                ClaimVerification(
                    claim=c,
                    status=ClaimStatus.UNSUPPORTED,
                    confidence=1.0,
                    evidence=[],
                    reason="No source context was provided to substantiate this claim.",
                )
                for c in claims
            ]
            return GroundingReport(
                total_claims=len(claims),
                supported_claims=0,
                unsupported_claims=len(claims),
                contradictory_claims=0,
                grounding_ratio=0.0,
                hallucination_rate=1.0,
                passed=False,
                claims=verifications,
                summary="All claims are unsupported because no context was retrieved.",
            )

        # Attempt LLM judge verification if LLM provider is available
        if self._llm is not None:
            try:
                return await self._verify_with_llm(
                    claims=claims,
                    actual_answer=actual_answer,
                    retrieved_context=retrieved_context,
                    threshold=effective_threshold,
                    question=question,
                )
            except Exception as e:
                logger.warning(
                    "LLM hallucination verification failed (%s). Falling back to deterministic.",
                    e,
                )

        # Deterministic verification fallback
        return self._verify_deterministic(
            claims=claims,
            retrieved_context=retrieved_context,
            threshold=effective_threshold,
        )

    def _verify_deterministic(
        self,
        claims: list[ExtractedClaim],
        retrieved_context: Sequence[str],
        threshold: float,
    ) -> GroundingReport:
        """Deterministic lexical and overlap-based evidence verification."""
        verifications: list[ClaimVerification] = []

        for claim in claims:
            claim_tokens = _tokenize(claim.claim_text)
            claim_token_set = set(claim_tokens)
            claim_has_negation = bool(claim_token_set & _NEGATION_WORDS)

            best_evidence: EvidenceCitation | None = None
            best_overlap = 0.0
            is_contradiction = False

            for idx, context_chunk in enumerate(retrieved_context):
                chunk_tokens = _tokenize(context_chunk)
                if not chunk_tokens:
                    continue

                chunk_token_set = set(chunk_tokens)
                chunk_has_negation = bool(chunk_token_set & _NEGATION_WORDS)

                # Content overlap calculation
                overlap = len(claim_token_set & chunk_token_set)
                recall = overlap / len(claim_token_set) if claim_token_set else 0.0

                if recall > best_overlap:
                    best_overlap = recall
                    # Extract best matching sentence as citation
                    citation_snippet = self._find_best_citation(claim.claim_text, context_chunk)
                    best_evidence = EvidenceCitation(
                        context_index=idx,
                        citation_text=citation_snippet,
                        similarity_score=round(recall, 3),
                    )

                # Check potential contradiction (polar opposite negation with high overlap)
                if recall >= 0.5 and (claim_has_negation != chunk_has_negation):
                    is_contradiction = True

            # Determine status based on overlap and polarity
            if is_contradiction and best_overlap >= 0.5:
                status = ClaimStatus.CONTRADICTORY
                confidence = round(best_overlap, 3)
                reason = (
                    "Claim contradicts context: opposing polarity or negation detected "
                    "in matching passage."
                )
            elif best_overlap >= 0.6:
                status = ClaimStatus.SUPPORTED
                confidence = round(best_overlap, 3)
                reason = (
                    f"Substantiated with high lexical alignment ({best_overlap:.1%}) "
                    "in retrieved context."
                )
            else:
                status = ClaimStatus.UNSUPPORTED
                confidence = round(1.0 - best_overlap, 3)
                reason = (
                    f"Insufficient grounding in source context (max overlap: {best_overlap:.1%})."
                )

            evidence_list = [best_evidence] if best_evidence and best_overlap >= 0.3 else []

            verifications.append(
                ClaimVerification(
                    claim=claim,
                    status=status,
                    confidence=confidence,
                    evidence=evidence_list,
                    reason=reason,
                )
            )

        return self._aggregate_report(verifications, threshold)

    async def _verify_with_llm(
        self,
        claims: list[ExtractedClaim],
        actual_answer: str,
        retrieved_context: Sequence[str],
        threshold: float,
        question: str | None,
    ) -> GroundingReport:
        """LLM-as-a-judge claim verification with structured output."""
        claims_formatted = "\n".join(f"- [{c.claim_id}]: {c.claim_text}" for c in claims)
        context_formatted = "\n".join(
            f"[{i}]: {chunk}" for i, chunk in enumerate(retrieved_context)
        )

        prompt = (
            "You are a strict TEVV (Testing, Evaluation, Verification, and Validation) evaluator.\n"
            "Analyze whether each claim in the answer is grounded in the retrieved context "
            "passages.\n\n"
            f"USER QUESTION: {question or 'N/A'}\n"
            f"FULL ANSWER: {actual_answer}\n\n"
            f"RETRIEVED CONTEXT PASSAGES:\n{context_formatted}\n\n"
            f"CLAIMS TO VERIFY:\n{claims_formatted}\n\n"
            "For each claim, determine:\n"
            "1. status: 'supported' (directly substantiated), "
            "'contradictory' (directly conflicts with context), or "
            "'unsupported' (absent or speculative).\n"
            "2. confidence: float between 0.0 and 1.0.\n"
            "3. evidence: list of cited context passages with context_index and citation_text.\n"
            "4. reason: concise explanation.\n\n"
            "Output JSON ONLY in this format:\n"
            "{\n"
            '  "summary": "<overall summary>",\n'
            '  "claims": [\n'
            '    {"claim_id": "claim-1", "status": "supported", "confidence": 0.95, '
            '"evidence": [{"context_index": 0, "citation_text": "...", "similarity_score": 0.9}], '
            '"reason": "..."}\n'
            "  ]\n"
            "}"
        )

        assert self._llm is not None
        raw_output = self._llm.generate(prompt=prompt, context=list(retrieved_context))
        payload = _extract_json_payload(raw_output)

        raw_claim_results = payload.get("claims")
        if not isinstance(raw_claim_results, list) or not raw_claim_results:
            raise ValueError("LLM response did not contain valid claims verification list.")

        results_by_id: dict[str, dict[str, object]] = {
            str(item.get("claim_id")): item
            for item in raw_claim_results
            if isinstance(item, dict) and "claim_id" in item
        }

        verifications: list[ClaimVerification] = []
        for claim in claims:
            item = results_by_id.get(claim.claim_id)
            if item is None:
                # Fall back to deterministic for unlisted claim
                det_report = self._verify_deterministic([claim], retrieved_context, threshold)
                verifications.append(det_report.claims[0])
                continue

            raw_status = str(item.get("status", "unsupported")).lower()
            if raw_status == "supported":
                status = ClaimStatus.SUPPORTED
            elif raw_status == "contradictory":
                status = ClaimStatus.CONTRADICTORY
            else:
                status = ClaimStatus.UNSUPPORTED

            raw_conf = item.get("confidence")
            if isinstance(raw_conf, (int, float, str)):
                try:
                    confidence = float(raw_conf)
                except (ValueError, TypeError):
                    confidence = 0.8
            else:
                confidence = 0.8
            confidence = max(0.0, min(1.0, confidence))

            citations: list[EvidenceCitation] = []
            raw_evidence = item.get("evidence")
            if isinstance(raw_evidence, list):
                for ev in raw_evidence:
                    if isinstance(ev, dict) and "citation_text" in ev:
                        raw_idx = ev.get("context_index", 0)
                        try:
                            idx = int(raw_idx) if isinstance(raw_idx, (int, float, str)) else 0
                        except (ValueError, TypeError):
                            idx = 0

                        raw_sim = ev.get("similarity_score", confidence)
                        try:
                            sim = (
                                float(raw_sim)
                                if isinstance(raw_sim, (int, float, str))
                                else confidence
                            )
                        except (ValueError, TypeError):
                            sim = confidence

                        citations.append(
                            EvidenceCitation(
                                context_index=idx,
                                citation_text=str(ev.get("citation_text")),
                                similarity_score=max(0.0, min(1.0, sim)),
                            )
                        )

            reason = str(item.get("reason", "Verified via LLM reasoning."))

            verifications.append(
                ClaimVerification(
                    claim=claim,
                    status=status,
                    confidence=confidence,
                    evidence=citations,
                    reason=reason,
                )
            )

        summary = str(payload.get("summary", "LLM-verified grounding assessment."))
        return self._aggregate_report(verifications, threshold, summary=summary)

    def _find_best_citation(self, claim_text: str, context_chunk: str) -> str:
        """Extract the sentence in context_chunk that best aligns with claim_text."""
        sentences = re.split(r"(?<=[.!?])\s+", context_chunk.strip())
        claim_tokens = set(_tokenize(claim_text))

        best_sentence = context_chunk[:150]
        max_overlap = -1

        for sent in sentences:
            sent_tokens = set(_tokenize(sent))
            overlap = len(claim_tokens & sent_tokens)
            if overlap > max_overlap:
                max_overlap = overlap
                best_sentence = sent.strip()

        return best_sentence

    def _aggregate_report(
        self,
        verifications: list[ClaimVerification],
        threshold: float,
        summary: str | None = None,
    ) -> GroundingReport:
        """Calculate aggregate counts, ratios, and pass/fail decision."""
        total = len(verifications)
        supported = sum(1 for v in verifications if v.status == ClaimStatus.SUPPORTED)
        unsupported = sum(1 for v in verifications if v.status == ClaimStatus.UNSUPPORTED)
        contradictory = sum(1 for v in verifications if v.status == ClaimStatus.CONTRADICTORY)

        grounding_ratio = round(supported / total, 3) if total > 0 else 1.0
        hallucination_rate = round((unsupported + contradictory) / total, 3) if total > 0 else 0.0

        passed = grounding_ratio >= threshold and contradictory == 0

        if summary is None:
            if contradictory > 0:
                summary = (
                    f"FAILED: Found {contradictory} contradictory and {unsupported} unsupported "
                    f"claims out of {total} total claims."
                )
            elif not passed:
                summary = (
                    f"FAILED: Grounding ratio {grounding_ratio:.1%} is below threshold "
                    f"{threshold:.1%}. ({unsupported} ungrounded claims)."
                )
            else:
                summary = (
                    f"PASSED: {supported}/{total} claims substantiated "
                    f"({grounding_ratio:.1%} grounded, 0 contradictions)."
                )

        return GroundingReport(
            total_claims=total,
            supported_claims=supported,
            unsupported_claims=unsupported,
            contradictory_claims=contradictory,
            grounding_ratio=grounding_ratio,
            hallucination_rate=hallucination_rate,
            passed=passed,
            claims=verifications,
            summary=summary,
        )
