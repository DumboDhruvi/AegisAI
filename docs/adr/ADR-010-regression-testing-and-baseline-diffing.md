# ADR-010: Regression Testing, Baseline Persistence, and Quality Gate Diffing

- **Status:** Accepted
- **Date:** 2026-09-16
- **Decision Makers:** Human Engineer & AegisAI Assistant

## Context
Module 9 specifies automated regression testing capabilities for AegisAI. As system prompts, embedding models, vector index parameters, chunking strategies, or model checkpoints change over time, evaluation metrics can silently degrade.

To prevent quality regressions in continuous integration and deployment pipelines, AegisAI requires:
1. Versioned snapshot persistence for reference baseline metrics.
2. Granular metric comparison between candidate runs and established baselines.
3. Configurable regression tolerance margins (default 5% drop limit).
4. Automated pass/fail quality gating to block non-compliant releases.

## Decision
1. **Domain Models (`src/aegis/domain/models/regression.py`):**
   - `RegressionStatus`: Enum designating metric outcome (`IMPROVEMENT`, `STABLE`, `REGRESSION`).
   - `BaselineRecord`: Immutable snapshot storing baseline ID, dataset version, model ID, metric mapping, timestamp, and run metadata.
   - `RegressionComparison`: Metric-level diff tracking baseline vs current score, delta, allowed drop tolerance, status, pass/fail boolean, and human-readable diagnostic message.
   - `RegressionReport`: Aggregate quality gate report assessing overall pass/fail status and providing an executive diagnostic summary.
2. **Services (`src/aegis/services/regression_engine.py`):**
   - `BaselineStore`: In-memory and disk-backed persistence store for baseline records with JSON serialization and corrupt-file resilience.
   - `RegressionEngine`: Compares current metrics against target baseline. Flags drops beyond `max_allowed_drop` as regressions, recognizes improvements and stable scores, and fails missing expected metrics.
3. **FastAPI Endpoints (`src/aegis/api/routes/regression.py`):**
   - `GET /api/v1/regression/baselines`: Lists registered baseline snapshots.
   - `GET /api/v1/regression/baseline/{id}`: Retrieves a baseline snapshot.
   - `POST /api/v1/regression/baseline`: Stores a new baseline snapshot.
   - `POST /api/v1/regression/compare`: Runs regression diff analysis and returns `RegressionReport`.

## Consequences
- **Positive:**
  - Automated CI/CD guardrail prevents releasing degraded AI models or configurations.
  - Transparent per-metric diffing pinpoints exact quality drops (e.g. faithfulness vs recall).
  - Flexible tolerance thresholds accommodate acceptable non-critical variance.
- **Trade-offs:**
  - Strict absence of metrics in current runs triggers critical failure; candidate runs must evaluate the complete metric suite expected by the baseline.
