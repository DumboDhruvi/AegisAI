# ADR-005: Rubric System — Multi-Criteria Scoring and Weighted Evaluation Engine

- **Status:** Accepted
- **Date:** 2026-09-15
- **Decision Makers:** Human Engineer & AegisAI Assistant

## Context
Module 4 requires a Rubric System providing explicit scoring criteria with customizable weights.
- Multi-dimensional scoring (e.g., accuracy, tone, safety, conciseness, grounding).
- Configurable scales (e.g., 1–5 integer scales or normalized continuous 0.0–1.0).
- Weighted criterion aggregation yielding a composite normalized score.
- Support for customizable rubric templates and runtime evaluation with LLM judges and deterministic fallbacks.

## Decision
1. **Domain Models (`src/aegis/domain/models/rubric.py`):**
   - `RubricCriterion`: Defines an individual evaluation dimension with `id`, `name`, `description`, `weight` (positive float), `scale_min`, `scale_max`, and score guidelines.
   - `RubricDefinition`: Bundles multiple criteria with a validation rule that weights must sum to a positive number, providing normalized weight calculation and overall passing thresholds.
   - `RubricScoreResult`: Captures criterion-level scores, diagnostic feedback, weighted overall score, and passing status.
   - Built-in templates: `DEFAULT_5_POINT_RUBRIC` (accuracy, tone, conciseness, safety) and `GROUNDING_RUBRIC` (factual grounding, context completeness, hallucination absence).
2. **Rubric Engine Service (`src/aegis/services/rubric_engine.py`):**
   - Registry for custom and predefined rubric definitions.
   - Async evaluation engine leveraging LLM structured output when an LLM provider is present, with an automated deterministic fallback when running offline or in CI/CD without API keys.
   - Composite weighted score aggregation: normalized to 0.0–1.0.
3. **REST API (`src/aegis/api/routes/rubrics.py`):**
   - `GET /api/v1/rubrics`: List all registered rubric definitions.
   - `GET /api/v1/rubrics/{rubric_id}`: Fetch a specific rubric definition.
   - `POST /api/v1/rubrics`: Register a custom rubric definition.
   - `POST /api/v1/rubrics/evaluate`: Evaluate input text or Q&A against a specified rubric.

## Consequences
- **Positive:**
  - Standardized enterprise evaluation criteria across diverse LLM tasks.
  - Transparent criteria weights and diagnostic feedback per criterion.
  - Clean separation between domain model definitions, evaluation service execution, and API transport.
- **Trade-offs:**
  - LLM judge evaluations incur latency per criterion if evaluated separately; addressed by scoring all criteria in a single structured prompt invocation.
