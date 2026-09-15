"""Unit tests for DashboardDataService (Module 14)."""

from __future__ import annotations

from aegis.services.dashboard_data import DashboardDataService, DashboardOverview


def test_dashboard_overview_metrics() -> None:
    """Test retrieving overview metrics."""
    service = DashboardDataService()
    overview = service.get_overview()
    assert isinstance(overview, DashboardOverview)
    assert 0.0 <= overview.overall_reliability <= 1.0
    assert 0.0 <= overview.faithfulness <= 1.0
    assert 0.0 <= overview.correctness <= 1.0
    assert 0.0 <= overview.relevance <= 1.0
    assert 0.0 <= overview.robustness <= 1.0
    assert 0.0 <= overview.hallucination_rate <= 1.0
    assert overview.total_evaluations >= overview.passed_evaluations


def test_dashboard_runs_data() -> None:
    """Test retrieving execution runs list."""
    service = DashboardDataService()
    runs = service.get_runs()
    assert len(runs) >= 1
    assert "run_id" in runs[0]
    assert "status" in runs[0]


def test_dashboard_failed_tests_data() -> None:
    """Test retrieving diagnostic failure records."""
    service = DashboardDataService()
    failures = service.get_failed_tests()
    assert len(failures) >= 1
    assert "diagnostic" in failures[0]
    assert "retrieved_context" in failures[0]


def test_dashboard_models_and_benchmarks() -> None:
    """Test model catalog and benchmarking data."""
    service = DashboardDataService()
    models = service.get_models()
    benchmarks = service.get_benchmarks()
    assert len(models) >= 1
    assert "input_price_per_m" in models[0]
    assert len(benchmarks) >= 1
    assert "composite_score" in benchmarks[0]


def test_dashboard_agents_and_regression() -> None:
    """Test agent trajectories and baseline regression records."""
    service = DashboardDataService()
    agents = service.get_agents()
    regressions = service.get_regression_baselines()
    assert len(agents) >= 1
    assert "tool_selection_f1" in agents[0]
    assert len(regressions) >= 1
    assert "delta" in regressions[0]
