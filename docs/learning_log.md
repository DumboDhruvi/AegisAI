# AegisAI — Engineering Learning Log

This document tracks technical learnings, architectural decisions, mistakes, and ecosystem discoveries across all module iterations.

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
