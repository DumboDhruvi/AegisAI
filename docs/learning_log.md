# AegisAI — Engineering Learning Log

This document tracks technical learnings, architectural decisions, mistakes, and ecosystem discoveries across all module iterations.

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
