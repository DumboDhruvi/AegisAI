"""Integration tests for Benchmarking FastAPI endpoints (Module 8)."""

from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from aegis.api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_api_list_models_endpoint(client: TestClient) -> None:
    """Verify GET /api/v1/benchmark/models returns pricing catalog."""
    response = client.get("/api/v1/benchmark/models")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, dict)
    assert "gpt-4o" in data
    assert "claude-3-5-sonnet" in data
    assert data["gpt-4o"]["input_cost_per_million"] == 2.50


def test_api_run_benchmark_endpoint(client: TestClient) -> None:
    """Verify POST /api/v1/benchmark/run executes comparative evaluation."""
    payload = {
        "dataset_name": "api-benchmark-test",
        "cases": [
            {
                "id": "c-1",
                "question": "What is Python?",
                "expected_answer": "Python is an interpreted programming language.",
                "context": ["Python is an interpreted, high-level language."],
            }
        ],
        "model_ids": ["mock-model-a", "mock-model-b"],
    }
    response = client.post("/api/v1/benchmark/run", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["dataset_name"] == "api-benchmark-test"
    assert "mock-model-a" in data["model_summaries"]
    assert "winner_model_id" in data
    assert len(data["recommendations"]) > 0
