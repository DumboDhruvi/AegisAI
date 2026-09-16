"""Integration tests for CI/CD Quality Gate API endpoints (Module 11)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aegis.api.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_api_get_default_thresholds(client: TestClient) -> None:
    """Test retrieving standard default quality gate thresholds."""
    resp = client.get("/api/v1/cicd/default-thresholds")
    assert resp.status_code == 200
    data = resp.json()
    assert data["min_faithfulness"] == 0.90
    assert data["min_correctness"] == 0.85
    assert data["max_hallucination_rate"] == 0.05


def test_api_evaluate_gates(client: TestClient) -> None:
    """Test evaluating quality gates via API."""
    payload = {
        "faithfulness": 0.94,
        "correctness": 0.88,
        "hallucination_rate": 0.02,
        "latency_p95_ms": 1500.0,
    }
    resp = client.post("/api/v1/cicd/evaluate-gates", json=payload)
    assert resp.status_code == 200
    gates = resp.json()
    assert len(gates) == 4
    assert all(g["passed"] is True for g in gates)


def test_api_run_pipeline_check(client: TestClient) -> None:
    """Test executing full CI/CD pipeline candidate evaluation via API."""
    payload = {
        "pipeline_id": "api-ci-101",
        "git_commit": "c0ffee1",
        "branch": "feature/m11-cicd-pipeline",
        "unit_tests_passed": True,
        "integration_tests_passed": True,
        "current_metrics": {
            "faithfulness": 0.93,
            "correctness": 0.87,
            "hallucination_rate": 0.03,
        },
        "metadata": {"triggered_by": "pull_request"},
    }
    resp = client.post("/api/v1/cicd/run-pipeline-check", json=payload)
    assert resp.status_code == 200
    report = resp.json()
    assert report["pipeline_id"] == "api-ci-101"
    assert report["overall_passed"] is True
    assert report["ai_evaluation_passed"] is True
    assert "CI/CD PIPELINE PASSED" in report["summary"]
