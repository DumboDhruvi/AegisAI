# ADR-013: Observability, Distributed Tracing, and Diagnostic Replay for Failed Evaluations

- **Status:** Accepted
- **Date:** 2026-09-16
- **Decision Makers:** Human Engineer & AegisAI Assistant

## Context
Module 12 addresses deep observability, runtime telemetry, and failure diagnostics. In complex generative AI systems:
1. Evaluation failures (e.g. low faithfulness, hallucination spikes, latency violations) are difficult to debug after the fact without exact execution context.
2. Debugging requires recording the full execution lifecycle: request ID, model name, prompt, retrieved contexts, tool calls, latencies, token consumption, cost, generated text, and metric results.
3. Teams need a seamless mechanism to extract reproduction payloads for failed runs so engineers can immediately replay the exact inputs and isolate whether the failure originated in retrieval, tool execution, or model inference.

## Decision
1. **Domain Models (`src/aegis/domain/models/observability.py`):**
   - `SpanType`: Categorical span classification (`REQUEST`, `RETRIEVAL`, `TOOL_CALL`, `LLM_INFERENCE`, `EVALUATION`).
   - `TraceSpan`: Sub-operation timing and attribute telemetry.
   - `EvaluationTraceRecord`: Immutable holistic record capturing inputs, retrieved chunks, tool calls, latency breakdown, tokens, USD costs, output answer, evaluation results, and pass/fail flag.
   - `TraceFilter`: Structured query filter for locating failed or high-cost runs.
   - `TraceSummary`: High-level operational aggregations (total traces, failure rate, mean latency, total tokens, total spend).
2. **Services (`src/aegis/services/observability_tracer.py`):**
   - `ObservabilityTracer`: In-memory and disk-persisted trace repository with filtering, summary aggregations, and automated diagnostic reproduction artifact generation.
3. **FastAPI Endpoints (`src/aegis/api/routes/observability.py`):**
   - `POST /api/v1/observability/trace`
   - `GET /api/v1/observability/trace/{run_id}`
   - `GET /api/v1/observability/traces`
   - `GET /api/v1/observability/summary`
   - `GET /api/v1/observability/reproduce/{run_id}`

## Consequences
- **Positive:**
  - Full reproducibility: zero guesswork when debugging degraded or failing test cases.
  - Complete financial and operational auditability across all generative runs.
  - Interoperable JSON serialization suitable for export to OpenTelemetry or external log drains.
- **Trade-offs:**
  - Recording full retrieved chunks for every production run increases storage requirements; production retention policies should prune or archive old passing traces while retaining failed traces for diagnostics.
