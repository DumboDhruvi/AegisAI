# ADR-004: Evaluation Engine Architecture — Dual Deterministic & LLM-as-a-Judge Evaluation

- **Status:** Accepted
- **Date:** 2026-09-15
- **Decision Makers:** Human Engineer & AegisAI Assistant

## Context
Module 3 specifies the core Evaluation Engine:
- **Input:** `question`, `expected_answer`, `AI answer`, `retrieved context`
- **Output:** `score` (0.0 to 1.0), `pass/fail` boolean, `reason` diagnostic explanation
- **Metrics:** Correctness, Relevance, and Faithfulness (groundedness).

In enterprise AI testing, relying solely on external LLM judges makes test execution slow, costly, and flaky in CI/CD. Conversely, relying solely on exact keyword matching fails to capture nuance and semantic equivalency.

## Decision
1. **Separation via Evaluator Protocol (`Evaluator`):**
   - Defined `Evaluator` protocol with `evaluate(input_data: EvaluationInput, threshold: float | None) -> MetricResult`.
   - All metric calculators return strongly typed `MetricResult` containing normalized scores, pass/fail booleans, thresholds, and diagnostic reasoning.
2. **Dual Metric Strategy:**
   - **Deterministic Evaluators (Sub-millisecond & zero cost):**
     - `F1CorrectnessEvaluator`: Token-level precision, recall, and harmonic F1 score against ground truth.
     - `LexicalFaithfulnessEvaluator`: Clause-level grounding verification measuring claim overlap against retrieved context chunks.
     - `KeywordRelevanceEvaluator`: Salient question concept coverage in the answer.
   - **LLM-as-a-Judge Evaluators (Deep semantic reasoning):**
     - `LlmFaithfulnessJudge`: Hallucination and ungrounded claim detection via structured JSON prompts.
     - `LlmCorrectnessJudge`: Semantic correctness comparison against ground truth.
     - `LlmAnswerRelevanceJudge`: Question answering directness and focus.
3. **Evaluation Engine (`EvaluationEngine`):**
   - Coordinates concurrent evaluation runs (`asyncio.gather`).
   - Supports custom metric weighting and threshold overrides.
   - Generates unified `EvaluationResult` composites.
4. **FastAPI Endpoints:**
   - Exposed `/api/v1/evaluate/case`, `/api/v1/evaluate/batch`, and `/api/v1/evaluate/metrics`.

## Consequences
- **Positive:**
  - Fast, deterministic evaluation runs in milliseconds for local testing and CI/CD.
  - Deep semantic reasoning available seamlessly when an LLM provider is configured.
  - Extensible foundation ready for rubric-based scoring (Module 4) and DeepEval integration.
- **Trade-offs:**
  - Lexical overlap metrics do not detect complex paraphrased synonyms without an LLM or embedding judge.
