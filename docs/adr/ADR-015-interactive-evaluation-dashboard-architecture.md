# ADR-015: Interactive Multi-Tab Evaluation and Diagnostic Dashboard

- **Status:** Accepted
- **Date:** 2026-09-16
- **Decision Makers:** Human Engineer & AegisAI Assistant

## Context
Module 14 specifies an interactive evaluation dashboard for AegisAI. Machine learning and platform engineers need a consolidated, visual control plane to:
1. Inspect high-level system reliability and quality metrics (faithfulness, correctness, relevance, robustness, hallucination rate).
2. Browse historical execution runs and query run-level telemetry.
3. Drill down into failed tests with exact prompt, retrieved context, and root-cause diagnostics.
4. Compare model latency and pricing profiles to evaluate Pareto cost-efficiency trade-offs.
5. Inspect multi-step autonomous agent trajectories, tool selection F1 scores, sequence alignment, and looping penalties.
6. Verify regression diffs and quality gate status against established reference baselines.

## Decision
1. **Architecture & Framework:**
   - Standardized on Streamlit (`src/aegis/dashboard/app.py`) for rapid interactive visualization without heavyweight frontend toolchains.
   - Decoupled presentation from business logic via `DashboardDataService` (`src/aegis/services/dashboard_data.py`), enabling deterministic unit testing and mocking.
2. **Dashboard Layout & Seven Dedicated Tabs:**
   - **Overview:** Executive KPI cards (Reliability, Faithfulness, Correctness, Relevance, Robustness, Hallucination) and radar/bar charts.
   - **Runs:** Filterable tabular view of historical execution runs with latency, token usage, cost, and pass/fail indicators.
   - **Failed Tests:** Accordion-based failure triage displaying model name, failed metric cutoff, retrieved context snippet, and root-cause diagnostic.
   - **Models:** Latency (mean & P95) and token pricing comparison matrix.
   - **Benchmarks:** Pareto frontier analysis identifying highest-quality and most cost-effective models.
   - **Agents:** Multi-step autonomous agent execution trajectories with tool selection F1, sequence alignment LCS, and loop detection penalties.
   - **Regression:** Baseline diffs with score deltas and pass/fail quality gate badges.

## Consequences
- **Positive:**
  - Zero-friction operational visibility: non-technical stakeholders and engineers share a common interface for AI reliability.
  - Complete testability: dashboard components and data services are fully tested without requiring a browser daemon.
- **Trade-offs:**
  - Streamlit reruns scripts on interaction; cached data services ensure minimal compute overhead during tab switching.
