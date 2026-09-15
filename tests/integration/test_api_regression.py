"""Integration tests for Regression Testing API endpoints (Module 9)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aegis.api.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_api_baseline_lifecycle(client: TestClient) -> None:
    """Test saving, retrieving, and listing baselines via API."""
    # List initial baselines
    resp = client.get("/api/v1/regression/baselines")
    assert resp.status_code == 200

    # Save a baseline
    payload = {
        "baseline_id": "api-base-v1",
        "dataset_version": "v1.0",
        "model_id": "gpt-4o-mini",
        "metrics": {"faithfulness": 0.88, "answer_relevance": 0.82},
        "metadata": {"author": "qa-team"},
    }
    create_resp = client.post("/api/v1/regression/baseline", json=payload)
    assert create_resp.status_code == 201
    assert create_resp.json()["baseline_id"] == "api-base-v1"

    # Retrieve saved baseline
    get_resp = client.get("/api/v1/regression/baseline/api-base-v1")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["baseline_id"] == "api-base-v1"
    assert data["metrics"]["faithfulness"] == 0.88

    # List baselines includes new baseline
    list_resp = client.get("/api/v1/regression/baselines")
    assert list_resp.status_code == 200
    assert "api-base-v1" in list_resp.json()


def test_api_get_baseline_not_found(client: TestClient) -> None:
    """Test 404 response for non-existent baseline ID."""
    resp = client.get("/api/v1/regression/baseline/unknown-base-999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_api_compare_regression_pass(client: TestClient) -> None:
    """Test regression comparison endpoint resulting in passed quality gate."""
    # Ensure baseline exists
    baseline_payload = {
        "baseline_id": "api-base-pass",
        "dataset_version": "v1.0",
        "model_id": "gpt-4o-mini",
        "metrics": {"faithfulness": 0.85, "answer_relevance": 0.80},
    }
    client.post("/api/v1/regression/baseline", json=baseline_payload)

    compare_payload = {
        "baseline_id": "api-base-pass",
        "current_version": "release-2.0",
        "current_metrics": {"faithfulness": 0.87, "answer_relevance": 0.81},
        "max_allowed_drop": 0.05,
    }
    resp = client.post("/api/v1/regression/compare", json=compare_payload)
    assert resp.status_code == 200
    result = resp.json()
    assert result["has_regression"] is False
    assert result["passed"] is True
    assert len(result["comparisons"]) == 2
    assert "QUALITY GATE PASSED" in result["summary"]


def test_api_compare_regression_fail(client: TestClient) -> None:
    """Test regression comparison endpoint resulting in failed quality gate."""
    baseline_payload = {
        "baseline_id": "api-base-fail",
        "dataset_version": "v1.0",
        "model_id": "gpt-4o-mini",
        "metrics": {"faithfulness": 0.90, "context_recall": 0.85},
    }
    client.post("/api/v1/regression/baseline", json=baseline_payload)

    # Faithfulness dropped by 0.15 (exceeds 0.05 margin)
    compare_payload = {
        "baseline_id": "api-base-fail",
        "current_version": "release-2.1",
        "current_metrics": {"faithfulness": 0.75, "context_recall": 0.85},
        "max_allowed_drop": 0.05,
    }
    resp = client.post("/api/v1/regression/compare", json=compare_payload)
    assert resp.status_code == 200
    result = resp.json()
    assert result["has_regression"] is True
    assert result["passed"] is False
    assert "QUALITY GATE FAILED" in result["summary"]


def test_api_compare_regression_not_found(client: TestClient) -> None:
    """Test 404 response when comparing against missing baseline."""
    compare_payload = {
        "baseline_id": "nonexistent-base",
        "current_version": "v1.0",
        "current_metrics": {"faithfulness": 0.90},
    }
    resp = client.post("/api/v1/regression/compare", json=compare_payload)
    assert resp.status_code == 404
