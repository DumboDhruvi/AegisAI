# ADR-012: Automated CI/CD AI Quality Gates, Pull Request Verification, and Baseline Diffing

- **Status:** Accepted
- **Date:** 2026-09-16
- **Decision Makers:** Human Engineer & AegisAI Assistant

## Context
Module 11 specifies continuous integration and continuous deployment (CI/CD) automation for AegisAI. Traditional software CI pipelines only test code logic (e.g. pytest, type checks, linting). However, in enterprise AI applications:
1. Code changes to prompts, chunk sizes, vector retrievers, or model backends can pass all deterministic software tests while causing silent regressions in generation quality.
2. Production reliability requires automated AI quality gates (e.g., faithfulness $\ge 0.90$, correctness $\ge 0.85$, hallucination rate $\le 5\%$, P95 latency $\le 2500$ms).
3. Candidate pull requests must compare their evaluated metrics against approved production baselines to detect subtle performance or quality degradation.

## Decision
1. **Domain Models (`src/aegis/domain/models/cicd.py`):**
   - `QualityGateThresholds`: Immutable configuration defining target bounds (`min_faithfulness`, `min_correctness`, `max_hallucination_rate`, `max_latency_p95_ms`, custom metric minimums, and `max_allowed_drop_from_baseline`).
   - `QualityGateEvaluation`: Result record for an individual gate checking target vs observed value.
   - `PipelineRunReport`: Aggregate CI/CD verdict encompassing unit tests, integration tests, AI quality gates, and baseline diffing.
2. **Services & CLI (`src/aegis/services/cicd_runner.py` & `src/aegis/cli/ci_gate.py`):**
   - `CicdRunner`: Orchestrates multi-stage evaluation across quality gates and baseline comparisons.
   - `ci_gate.py`: Standalone CLI utility callable directly from CI pipeline step scripts (e.g. GitHub Actions runner) with standard Unix exit codes (0 for pass, 1 for fail).
3. **FastAPI Endpoints (`src/aegis/api/routes/cicd.py`):**
   - `POST /api/v1/cicd/evaluate-gates`
   - `POST /api/v1/cicd/run-pipeline-check`
   - `GET /api/v1/cicd/default-thresholds`
4. **GitHub Actions (`.github/workflows/ci.yml`):**
   - Automated workflow triggered on `push` and `pull_request`.
   - Executes code formatting (ruff), linting (ruff), static typing (mypy), test suite with coverage $\ge 90\%$, and AI quality gate verification (`ci_gate.py`).

## Consequences
- **Positive:**
  - Shift-left AI reliability: quality and hallucination regressions are caught before PR merge.
  - Unified pipeline report providing clear diagnostic failure reasons for engineers.
  - Fully compatible with standard GitHub Actions and external webhook CI/CD runners.
- **Trade-offs:**
  - Running full LLM evaluation on every PR can add CI execution time; lightweight deterministic metrics and heuristic baselines should run on PRs, while full multi-model benchmarks can run on nightly schedules.
