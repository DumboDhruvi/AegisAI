"""Integration tests for Agent Evaluation FastAPI routes (Module 7)."""

from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from aegis.api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_api_evaluate_trajectory(client: TestClient) -> None:
    """Verify POST /api/v1/agent/evaluate-trajectory."""
    payload = {
        "task": "Find quarterly revenue and compute VAT.",
        "steps": [
            {
                "name": "database",
                "arguments": {"query": "SELECT revenue FROM q3", "table": "q3"},
                "output": "100000",
            },
            {
                "name": "calculator",
                "arguments": {"expression": "100000 * 0.20"},
                "output": "20000",
            },
        ],
        "final_answer": "Quarterly VAT is $20,000.",
        "expected_tools": ["database", "calculator"],
        "expected_sequence": ["database", "calculator"],
    }
    response = client.post("/api/v1/agent/evaluate-trajectory", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["tool_selection_score"] == 1.0
    assert data["tool_arguments_score"] == 1.0
    assert data["tool_sequence_score"] == 1.0
    assert data["task_completion_score"] == 1.0
    assert data["efficiency_score"] == 1.0
    assert data["passed"] is True
    assert data["overall_score"] >= 0.9


def test_api_simulate_and_evaluate(client: TestClient) -> None:
    """Verify POST /api/v1/agent/simulate-and-evaluate executes tools and scores trace."""
    payload = {
        "task": "Calculate compound interest.",
        "steps": [
            {
                "name": "calculator",
                "arguments": {"expression": "1000 * (1 + 0.05)**2"},
            }
        ],
        "final_answer": "The compounded amount is $1,102.50.",
        "expected_tools": ["calculator"],
        "expected_sequence": ["calculator"],
    }
    response = client.post("/api/v1/agent/simulate-and-evaluate", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["tool_selection_score"] == 1.0
    assert data["passed"] is True
    assert data["unnecessary_steps_count"] == 0
