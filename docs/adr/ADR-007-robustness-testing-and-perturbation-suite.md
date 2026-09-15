# ADR-007: Robustness Testing Architecture — Synthetic Perturbation and Comparative Adversarial Analysis

- **Status:** Accepted
- **Date:** 2026-09-15
- **Decision Makers:** Human Engineer & AegisAI Assistant

## Context
Module 6 requires automated testing of model robustness under degraded, noisy, or adversarial conditions:
- Typos and character noise
- Ambiguity and vague referents
- Missing information and truncated constraints
- Injected conflicting documents
- Irrelevant distractor passages
- Adversarial prompt injection attacks
- Out-of-domain queries
- Comparative performance analysis (baseline vs. perturbed degradation deltas)

Production enterprise evaluation cannot simply measure clean happy paths; systems must reliably fail gracefully, resist prompt injection, and retain retrieval quality in the presence of noise.

## Decision
1. **Domain Models (`src/aegis/domain/models/robustness.py`):**
   - `PerturbationType`: Categorical enumeration of all 7 specified perturbation strategies.
   - `PerturbedInput`: Data model containing original text, perturbed text, perturbation category, and metadata.
   - `RobustnessTestCase`: Paired `baseline_input` and `perturbed_input` for direct comparative benchmarking.
   - `PerturbationComparison`: Measures `baseline_score`, `perturbed_score`, `score_delta`, `degradation_ratio`, and quality gate pass/fail.
   - `RobustnessReport`: Composite suite report tracking total tests, degradation by category, and overall robustness index.
2. **Perturbation Engine (`PerturbationEngine`):**
   - Implements deterministic character manipulation via realistic QWERTY neighbor substitutions.
   - Entity neutralization for ambiguity testing.
   - Structural clause truncation for missing context testing.
   - Document injection pipelines for contradictory and irrelevant context chunks.
   - Adversarial prompt injection probe generation.
3. **Robustness Tester Service (`RobustnessTester`):**
   - Coordinates comparative execution between baseline and perturbed inputs using `EvaluationEngine`.
   - Gating logic: enforces maximum allowable degradation ratios (e.g. 25% max allowable drop).
4. **FastAPI Endpoints (`src/aegis/api/routes/robustness.py`):**
   - `POST /api/v1/robustness/perturb`: Generate perturbed variants on demand.
   - `POST /api/v1/robustness/evaluate-case`: Single paired comparative analysis.
   - `POST /api/v1/robustness/evaluate-suite`: Full benchmark suite execution across multiple inputs and categories.

## Consequences
- **Positive:**
  - Automated detection of brittle models vulnerable to simple typos or context noise.
  - Zero external dependencies: operates fully offline and deterministically.
  - Direct quantifiable degradation metrics for regression tracking.
- **Trade-offs:**
  - Synthetic typos use QWERTY adjacency; semantic paraphrase perturbation is handled via ambiguity templates and LLM evaluation.
