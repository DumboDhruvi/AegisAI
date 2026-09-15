# ADR-009: Multi-Model Comparative Benchmarking — Accuracy, Faithfulness, Relevance, Latency, Token Usage, and Cost

- **Status:** Accepted
- **Date:** 2026-09-15
- **Decision Makers:** Human Engineer & AegisAI Assistant

## Context
Module 8 specifies running identical datasets against multiple models to enable objective comparison across:
1. Accuracy
2. Faithfulness
3. Relevance
4. Hallucination rate
5. Latency (mean and P95)
6. Token usage (prompt, completion, total)
7. Financial cost (USD based on model token pricing)

Enterprise AI deployments require empirical trade-off analysis between frontier model accuracy (e.g. GPT-4o, Claude 3.5 Sonnet) and compact cost-effective alternatives (e.g. GPT-4o-mini, Gemini 1.5 Flash).

## Decision
1. **Domain Models (`src/aegis/domain/models/benchmark.py`):**
   - `ModelPricing`: Defines per-million input and output token pricing.
   - `ModelExecutionResult`: Granular test-case level execution metrics (accuracy, faithfulness, relevance, hallucination rate, latency in ms, token usage, computed USD cost).
   - `ModelBenchmarkSummary`: Aggregated performance profile (mean quality metrics, mean & P95 latency, total tokens, total cost, composite score).
   - `BenchmarkComparisonReport`: Complete multi-model comparative report with winner selection and cost-efficiency trade-off recommendations.
2. **Benchmarking Service (`BenchmarkingService`):**
   - Industry-standard model pricing catalog (`gpt-4o`, `gpt-4o-mini`, `claude-3-5-sonnet`, `gemini-1.5-pro`, `gemini-1.5-flash`, mock models).
   - Character-to-token heuristic estimation (`estimate_tokens`).
   - Integrated quality scoring reusing `EvaluationEngine` and `HallucinationDetector`.
   - Automated Pareto frontier evaluation: identifies highest quality winner and highlights cost-effective alternatives with quantified trade-offs.
3. **FastAPI Endpoints (`src/aegis/api/routes/benchmark.py`):**
   - `GET /api/v1/benchmark/models`: Retrieve pricing catalog and model list.
   - `POST /api/v1/benchmark/run`: Run comparative benchmark over test cases.

## Consequences
- **Positive:**
  - Objective, quantifiable basis for model selection in production.
  - Transparent ROI and cost per quality point metrics.
  - Unified evaluation reusing core metric engines.
- **Trade-offs:**
  - Token counts for non-mock models rely on standardized 4-character heuristics in offline environments; production integrations can bind native tokenizer libraries.
