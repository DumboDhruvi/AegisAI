# AegisAI — Engineering Learning Log

This document tracks technical learnings, architectural decisions, mistakes, and ecosystem discoveries across all module iterations.

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
