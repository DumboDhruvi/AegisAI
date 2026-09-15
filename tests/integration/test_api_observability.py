"""Integration tests for Observability and Tracing API endpoints (Module 12)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aegis.api.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_api_trace_lifecycle(client: TestClient) -> None:
    """Test recording, querying, and retrieving an execution trace."""
    trace_payload = {
        "run_id": "api-trace-1",
        "request_id": "req-api-1",
        "model_name": "gpt-4o",
        "prompt": "Summarize policy guidelines",
        "answer": "All employees must follow guidelines.",
        "evaluation_results": {"faithfulness": 0.94, "correctness": 0.91},
        "passed": True,
        "latency_ms": {"total": 280.0},
        "tokens": {"total": 85},
        "cost_usd": 0.0008,
    }

    # Record trace
    create_resp = client.post("/api/v1/observability/trace", json=trace_payload)
    assert create_resp.status_code == 201
    assert create_resp.json()["run_id"] == "api-trace-1"

    # Get single trace
    get_resp = client.get("/api/v1/observability/trace/api-trace-1")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["run_id"] == "api-trace-1"
    assert data["model_name"] == "gpt-4o"

    # Query traces with filter
    list_resp = client.get("/api/v1/observability/traces?model_name=gpt-4o&passed=true")
    assert list_resp.status_code == 200
    runs = list_resp.json()
    assert any(r["run_id"] == "api-trace-1" for r in runs)


def test_api_get_trace_not_found(client: TestClient) -> None:
    """Test 404 for unknown trace run_id."""
    resp = client.get("/api/v1/observability/trace/unknown-run-999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_api_summary_and_reproduce(client: TestClient) -> None:
    """Test summary operational metrics and diagnostic reproduction endpoints."""
    trace_payload = {
        "run_id": "api-trace-reproduce",
        "request_id": "req-api-rep",
        "model_name": "gpt-4o-mini",
        "prompt": "Explain database indexes",
        "answer": "Indexes speed up read queries.",
        "evaluation_results": {"faithfulness": 0.55, "correctness": 0.80},
        "passed": False,
        "latency_ms": {"total": 350.0},
        "tokens": {"total": 60},
        "cost_usd": 0.0002,
    }
    client.post("/api/v1/observability/trace", json=trace_payload)

    # Get summary
    summary_resp = client.get("/api/v1/observability/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["total_traces"] >= 1

    # Reproduce failed run
    rep_resp = client.get("/api/v1/observability/reproduce/api-trace-reproduce")
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()
    assert rep_data["run_id"] == "api-trace-reproduce"
    assert "faithfulness" in rep_data["failed_metrics"]


def test_api_reproduce_not_found(client: TestClient) -> None:
    """Test 404 for reproduction of non-existent run ID."""
    resp = client.get("/api/v1/observability/reproduce/missing-run-xyz")
    assert resp.status_code == 404
