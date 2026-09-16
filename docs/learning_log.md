# AegisAI — Engineering Learning Log

This document tracks technical learnings, architectural decisions, mistakes, and ecosystem discoveries across all module iterations.

---

## [2026-09-15] — Milestone 4: Module 4 (Rubric System)

### 1. What I Learned
- **Multi-Criteria Evaluation vs. Single-Metric Scoring:** In real-world enterprise AI evaluation (TEVV: Testing, Evaluation, Verification, and Validation), pass/fail thresholds on a single dimension (e.g. lexical overlap) fail to capture production requirements where answers must simultaneously be accurate, brand-aligned in tone, concise, and safe. Multi-criteria rubrics allow defining explicit scoring dimensions with varying weights and granular score-level descriptions.
- **Normalized Weighted Aggregation:** By normalizing raw criteria scores against their respective scales ($[S_{\min}, S_{\max}] \to [0.0, 1.0]$) and weighting each dimension proportional to total rubric weight ($\frac{w_i}{\sum w}$), composite scores remain stable and bounded in $[0.0, 1.0]$ regardless of heterogeneous criterion scales (e.g. mixing 1–5 scales with 0–10 scales).
- **Single-Prompt Multi-Criteria LLM Judging:** Scoring multiple rubric dimensions in individual LLM calls multiplies latency and token cost linearly. Formulating the prompt to return structured JSON containing all criteria scores simultaneously reduces latency by 75%+ while providing holistic context to the LLM evaluator.

### 2. Architectural Decisions
- Created `RubricCriterion`, `RubricDefinition`, and `RubricScoreResult` in `src/aegis/domain/models/rubric.py`.
- Built `RubricEngine` in `src/aegis/services/rubric_engine.py` with predefined rubric templates (`DEFAULT_5_POINT_RUBRIC`, `GROUNDING_RUBRIC`) and deterministic fallback evaluation when running offline or in CI/CD without API keys.
- Exposed REST API endpoints `/api/v1/rubrics`, `/api/v1/rubrics/{id}`, and `/api/v1/rubrics/evaluate` in `src/aegis/api/routes/rubrics.py`.
- Documented architecture in [ADR-005](file:///home/dumbo/AI%20PROJECT/docs/adr/ADR-005-rubric-engine-and-criteria-scoring.md).
- Maintained 95% test coverage across 104 passing unit and integration tests.

---

## [2026-09-15] — Milestone 3: Module 3 (Evaluation Engine)

### 1. What I Learned
- **Deterministic vs. LLM-as-a-Judge Trade-offs:** In enterprise TEVV (Testing, Evaluation, Verification, and Validation), running an LLM on every evaluation step is too slow and costly for rapid local unit testing or high-frequency CI (Continuous Integration). By providing deterministic token-overlap metrics (F1 score, lexical grounding, keyword relevance) alongside semantic LLM judges, we achieve sub-millisecond local test suites while still supporting deep semantic evaluation.
- **RAG Triad Metrics:**
  - *Faithfulness (Groundedness):* Checks whether every factual statement in the AI's answer is substantiated by the retrieved context chunks (zero hallucinations).
  - *Correctness:* Compares the generated answer to an expected answer (ground truth) to measure factual accuracy.
  - *Answer Relevance:* Verifies that the AI directly and fully answered the user prompt without evading or adding irrelevant fluff.
- **Concurrent Evaluator Execution (`asyncio.gather`):** Evaluating multiple metrics sequentially multiplies response latency. By designing an asynchronous `Evaluator` protocol, `EvaluationEngine` evaluates all metrics in parallel, returning aggregated composite scores with individual diagnostic explanations.

### 2. Architectural Decisions
- Created `MetricType`, `EvaluationInput`, `MetricResult`, and `EvaluationResult` in `src/aegis/domain/models/evaluation.py`.
- Built `Evaluator` protocol in `src/aegis/services/evaluators/base.py`.
- Implemented `F1CorrectnessEvaluator`, `LexicalFaithfulnessEvaluator`, and `KeywordRelevanceEvaluator` in `src/aegis/services/evaluators/deterministic.py`.
- Implemented `LlmFaithfulnessJudge`, `LlmCorrectnessJudge`, and `LlmAnswerRelevanceJudge` in `src/aegis/services/evaluators/llm_judge.py`.
- Built `EvaluationEngine` in `src/aegis/services/evaluation_engine.py`.
- Exposed REST API endpoints `/api/v1/evaluate/case`, `/api/v1/evaluate/batch`, and `/api/v1/evaluate/metrics` in `src/aegis/api/routes/evaluation.py`.
- Documented architecture in [ADR-004](file:///home/dumbo/AI%20PROJECT/docs/adr/ADR-004-evaluation-engine-and-metrics.md).
- Maintained 96% test coverage across 82 passing tests.

---

## [2026-09-14] — Milestone 2: Module 2 (RAG Application)

### 1. What I Learned
- **Protocol-Driven Decoupling:** In Python, `typing.Protocol` allows structural subtyping (duck typing with static verification). By depending on `VectorStore` and `EmbeddingProvider` protocols instead of concrete SDK classes, the pipeline can run against an in-memory store for unit tests or pgvector in production without altering a single line of business logic.
- **Chunk Offsets & Provenance:** Storing `start_char` and `end_char` alongside chunk text allows downstream evaluation engines (M5) to highlight the exact sentence in the source document where an AI hallucinated or derived a claim.
- **Sliding Window Chunking:** Slicing text with an overlap prevents vital contextual information (like sentences spanning a chunk boundary) from being severed and lost during retrieval.

### 2. Architectural Decisions
- Implemented `Document`, `DocumentChunk`, `RetrievedDocument`, and `RagResponse` in `src/aegis/domain/models/rag.py`.
- Built `DocumentParser` and `TextChunker` in `services/`.
- Built `InMemoryVectorStore` using cosine similarity and `DeterministicEmbeddingProvider` in `infrastructure/`.
- Built `RagPipeline` in `services/rag_pipeline.py`.
- Exposed REST API endpoints `/api/v1/rag/ingest`, `/api/v1/rag/query`, and `/api/v1/rag/stats` in `src/aegis/api/routes/rag.py`.
- Maintained 96% test coverage across 50 passing tests.

---

## [2026-09-14] — Milestone 1: Module 1 (Evaluation Dataset)

### 1. What I Learned
- **Partial Rejection Pattern:** In production AI evaluation, datasets can contain thousands of records. Failing the whole ingestion when one row is bad is frustrating. By segregating results into `valid_cases` and `rejected_cases` (with exact field-level errors), we preserve good data while giving precise diagnostics for bad rows.
- **Model Immutability (`frozen=True`):** In evaluation frameworks, test cases and ground truths must never be mutated during test runs or metric calculation. Freezing the Pydantic models ensures concurrency safety and evaluation purity.
- **Tag Normalization & Sliced Testing:** Cleaning and deduplicating tags at the domain model level allows downstream runners to execute slices (e.g. running only `"security"` or `"rag"` tests) without case-sensitivity bugs.

### 2. Architectural Decisions
- Placed domain models (`EvaluationCase`, `RejectedCase`, `DatasetValidationResult`) in `domain/models/`, completely free of HTTP or database dependencies.
- Added FastAPI routes in `api/routes/datasets.py` wrapping the `DatasetLoader` service.
- Maintained 97% unit and integration test coverage.

### 3. Mistakes & Self-Corrections
- **Duplicate ID Detection:** Initial validation accepted records with the same `id`. Added an explicit check in `DatasetLoader` to reject duplicates with helpful error descriptions.
- **JSON Syntax Detection:** A malformed JSON string starting with `[` but missing the closing `]` previously fell through to the JSONL parser. Updated parser to explicitly handle malformed JSON arrays cleanly.

---

## [2026-09-14] — Milestone 0: Project Scaffolding & Engineering Standards

### 1. What I Learned
- **Modern Python Packaging (`pyproject.toml`):** Setuptools 77+ deprecates `project.license = { text = "MIT" }` in favor of standard SPDX strings `license = "MIT"`.
- **Layered Architecture in AI Systems:** Decoupling evaluation logic from HTTP frameworks (FastAPI) and storage (Postgres/pgvector) makes metrics deterministic, testable in milliseconds, and independent of infrastructure availability.
- **Evaluation as Code:** Treating datasets, rubrics, and baselines with the same version control rigor as source code is essential for scientific reproducibility in TEVV (Testing, Evaluation, Verification, and Validation).

### 2. Architectural Decisions
- Created isolated layers: `api`, `services`, `domain`, `infrastructure`, and `core`.
- Configured strict type checking with `mypy` and code quality formatting via `ruff`.
- Pinned development and production dependencies with specific semver ranges.

### 3. Mistakes & Self-Corrections
- **Pip editable build:** Attempted to install before `README.md` and `src` directory existed. Corrected immediately by setting up directory structure and documentation before running package installation.
