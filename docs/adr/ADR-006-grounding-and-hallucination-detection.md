# ADR-006: Grounding & Hallucination Detection — Atomic Claim Verification & Evidence Attribution

- **Status:** Accepted
- **Date:** 2026-09-15
- **Decision Makers:** Human Engineer & AegisAI Assistant

## Context
Module 5 requires rigorous Grounding and Hallucination verification:
- For each generated claim in an AI response:
  - Claim $\to$ Evidence attribution.
  - Supported determination (`supported`, `contradictory`, `unsupported`).
  - Confidence scoring.
- Detection of unsupported claims and direct factual contradictions against retrieved source passages.
- In high-throughput evaluation, claim-level evaluation must operate deterministically without requiring external API calls, while also supporting deep semantic LLM-as-a-judge reasoning when available.

## Decision
1. **Domain Models (`src/aegis/domain/models/grounding.py`):**
   - `ClaimStatus`: Enum (`supported`, `contradictory`, `unsupported`).
   - `ExtractedClaim`: Represents an atomic proposition with `claim_id`, `claim_text`, `start_char`, and `end_char`.
   - `EvidenceCitation`: Links to context passage index, excerpt text, and similarity score.
   - `ClaimVerification`: Holds single claim determination, confidence score, evidence list, and diagnostic reason.
   - `GroundingReport`: Composite summary containing counts, `grounding_ratio`, `hallucination_rate`, `passed`, and diagnostic narrative.
2. **Claim Extractor (`ClaimExtractor`):**
   - Parses generated responses into atomic claim units.
   - Filters conversational boilerplate ("Hello!", "Sure thing.", "Hope this helps!") to avoid false ungrounded penalties on polite conversational filler.
   - Tracks exact character offsets in the response string.
3. **Hallucination Detector (`HallucinationDetector`):**
   - **Dual Strategy:**
     - Deterministic lexical/overlap evaluation with polarity/negation contradiction checking for offline and CI runs.
     - Single-prompt LLM structured claim verification when an LLM provider is active.
     - Automatic graceful fallback if LLM parsing fails.
   - Computes `grounding_ratio = supported / total` and `hallucination_rate = (unsupported + contradictory) / total`.
   - Rejects answers if `contradictory_claims > 0` or if `grounding_ratio < threshold`.
4. **FastAPI Endpoints (`src/aegis/api/routes/grounding.py`):**
   - `POST /api/v1/grounding/extract-claims`: Extract atomic claims with character offsets.
   - `POST /api/v1/grounding/verify`: Perform full grounding verification and evidence attribution against retrieved passages.

## Consequences
- **Positive:**
  - Granular, explainable attribution pinpointing exactly which sentences in an answer are substantiated, unsupported, or contradictory.
  - Sub-millisecond deterministic evaluation for high-velocity CI/CD tests.
  - Direct integration into RAG and Rubric workflows.
- **Trade-offs:**
  - Simple sentence tokenization may occasionally combine complex compound claims; sentence boundary regex provides an effective balance without adding heavy NLP dependencies.
