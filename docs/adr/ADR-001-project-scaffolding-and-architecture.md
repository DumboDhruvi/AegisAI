# ADR-001: Project Scaffolding, Package Layout, and Layered Architecture

- **Status:** Accepted
- **Date:** 2026-09-14
- **Decision Makers:** Human Engineer & AegisAI Assistant

## Context
AegisAI is an enterprise-grade AI Reliability and Evaluation platform. Production AI evaluation platforms suffer from high complexity due to non-deterministic model outputs, vector databases, varying embedding providers, and dynamic evaluation rubrics. Without strict architectural boundaries, code quickly becomes tightly coupled to specific databases or HTTP frameworks, making unit testing slow, unreliable, or dependent on live network calls.

## Decision
1. **Layered Architecture:**
   - `src/aegis/api`: FastAPI routes, schemas, and HTTP status codes.
   - `src/aegis/services`: Workflow orchestration and business transactions.
   - `src/aegis/domain`: Pure evaluation logic, metrics, and rubric evaluation (zero external I/O).
   - `src/aegis/infrastructure`: Adapters for PostgreSQL/pgvector, LLMs, and vector embeddings.
   - `src/aegis/core`: Configuration management (`pydantic-settings`) and logging.
2. **Standard Toolchain:**
   - Package management: `pyproject.toml` (PEP 518/621).
   - Formatting & Linting: `ruff`.
   - Type Checking: `mypy` with `strict = true`.
   - Testing: `pytest` with `pytest-asyncio` and `pytest-cov`.
3. **Dataset Versioning:**
   - Dedicated directory `evaluation/datasets/v{N}` to treat datasets as first-class versioned code assets.

## Alternatives Considered
- **Monolithic flat structure (`app.py`):** Rejected because it mixes HTTP routing with evaluation logic and storage, violating separation of concerns.
- **Poetry / Pipenv:** Rejected in favor of standard PEP 517/621 `pyproject.toml` with `pip` and `.venv`, ensuring minimal external tooling dependencies.

## Consequences
- **Positive:**
  - Fast, pure unit tests for domain evaluation logic without database or LLM network fixtures.
  - Reproducible environments and clear developer onboarding.
- **Trade-offs:**
  - Slightly more boilerplate initially (layer mapping and explicit DTOs/schemas).
